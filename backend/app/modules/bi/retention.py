"""
STEP 80: engagement, retention, and cohort analysis — all against real
users.created_at / users.last_login_at and Step 78's api_usage_metrics.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.factory import Factory
from app.models.user import User
from app.modules.admin.models import APIUsageMetric

ACTIVE_WINDOW_DAYS = 7
DEFAULT_COHORT_MONTHS = 6


def _add_months(dt: datetime, months: int) -> datetime:
    """No python-dateutil dependency in this project — plain month
    arithmetic with year rollover, which is all relativedelta was
    being used for here."""
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    return dt.replace(year=year, month=month)


def compute_weekly_active_factories(db: Session) -> dict:
    """North Star metric (docs/bi/metric-dictionary.md). api_usage_metrics
    is organization-scoped, not factory-scoped (Step 78's middleware
    records the caller's org, not which factory a request touched) — a
    factory counts as "active" if its organization made any API request
    in the window. A documented proxy, not a precise per-factory signal,
    since nothing in this codebase tracks factory_id per request today.
    """
    window_start = datetime.now(timezone.utc) - timedelta(days=ACTIVE_WINDOW_DAYS)

    active_org_ids = set(
        db.scalars(
            select(APIUsageMetric.organization_id).where(
                APIUsageMetric.period_start >= window_start
            )
        )
    )

    if not active_org_ids:
        return {"weekly_active_factories": 0, "active_organizations": 0}

    count = len(
        db.scalars(select(Factory.id).where(Factory.organization_id.in_(active_org_ids))).all()
    )

    return {"weekly_active_factories": count, "active_organizations": len(active_org_ids)}


def compute_cohort_retention(
    db: Session, cohort_months: int = DEFAULT_COHORT_MONTHS
) -> list[dict]:
    """
    A classic cohort table: each row is a signup month, each column is
    "still active N months later" (active = last_login_at fell within
    that later month). Only fills in columns that have actually
    elapsed — a cohort from last month can't have a "3 months later"
    number yet, and that's reported as null rather than 0%, so a
    dashboard doesn't mistake "hasn't happened yet" for "everyone churned".
    """
    now = datetime.now(timezone.utc)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    cohorts = []

    # range includes 0 (the current, still-in-progress month) — a
    # cohort that signed up this month is a real cohort with a real
    # (partial) month-0 retention number, not something to exclude
    # until the month closes.
    for months_back in range(cohort_months, -1, -1):
        cohort_start = _add_months(current_month_start, -months_back)
        cohort_end = _add_months(cohort_start, 1)

        cohort_user_ids = db.scalars(
            select(User.id).where(
                User.created_at >= cohort_start, User.created_at < cohort_end
            )
        ).all()

        cohort_size = len(cohort_user_ids)
        retention_by_offset = []

        max_offset = min(months_back, cohort_months)
        for offset in range(0, max_offset + 1):
            window_start = _add_months(cohort_start, offset)
            window_end = _add_months(window_start, 1)

            if window_start > now:
                break

            if cohort_size == 0:
                retention_by_offset.append({"month_offset": offset, "retained_percent": None})
                continue

            retained_total = len(
                db.scalars(
                    select(User.id).where(
                        User.id.in_(cohort_user_ids),
                        User.last_login_at >= window_start,
                        User.last_login_at < window_end,
                    )
                ).all()
            )
            retention_by_offset.append(
                {
                    "month_offset": offset,
                    "retained_percent": round(retained_total / cohort_size * 100, 1),
                }
            )

        cohorts.append(
            {
                "cohort_month": cohort_start.date().isoformat(),
                "cohort_size": cohort_size,
                "retention": retention_by_offset,
            }
        )

    return cohorts
