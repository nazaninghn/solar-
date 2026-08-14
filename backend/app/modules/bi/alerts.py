"""
STEP 80: KPI Alerts — real threshold checks against the same
computations app.modules.bi already exposes via API, not a separate
parallel definition of "what's wrong."
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.admin.models import APIUsageMetric
from app.modules.bi.funnel import compute_activation_rate
from app.models.factory import Factory

# Below these sample sizes, a percentage swing is noise, not signal —
# 3 signups going from 2/3 activated to 1/3 activated is a 33-point
# "drop" that means nothing.
MIN_ACTIVATION_COHORT_SIZE = 10
ACTIVATION_RATE_WARNING_THRESHOLD_PERCENT = 20.0

MIN_PRIOR_WEEK_ACTIVE_FACTORIES = 5
WEEK_OVER_WEEK_DECLINE_WARNING_PERCENT = 30.0


def _active_factories_in_window(db: Session, window_start: datetime, window_end: datetime) -> int:
    active_org_ids = set(
        db.scalars(
            select(APIUsageMetric.organization_id).where(
                APIUsageMetric.period_start >= window_start,
                APIUsageMetric.period_start < window_end,
            )
        )
    )
    if not active_org_ids:
        return 0
    return len(
        db.scalars(select(Factory.id).where(Factory.organization_id.in_(active_org_ids))).all()
    )


def check_kpi_alerts(db: Session) -> list[dict]:
    """Returns breaches found — pure computation, the caller (app.jobs.
    bi_jobs) decides what to do with them, matching app.modules.finops.
    service.check_budget_thresholds's shape."""
    breaches = []

    activation = compute_activation_rate(db, days=30)
    if (
        activation["cohort_size"] >= MIN_ACTIVATION_COHORT_SIZE
        and activation["activation_rate_percent"] < ACTIVATION_RATE_WARNING_THRESHOLD_PERCENT
    ):
        breaches.append(
            {
                "key": "LOW_ACTIVATION_RATE",
                "severity": "WARNING",
                "detail": (
                    f"30-day activation rate is {activation['activation_rate_percent']}% "
                    f"(cohort of {activation['cohort_size']}), below the "
                    f"{ACTIVATION_RATE_WARNING_THRESHOLD_PERCENT}% warning threshold"
                ),
            }
        )

    now = datetime.now(timezone.utc)
    this_week = _active_factories_in_window(db, now - timedelta(days=7), now)
    prior_week = _active_factories_in_window(db, now - timedelta(days=14), now - timedelta(days=7))

    if prior_week >= MIN_PRIOR_WEEK_ACTIVE_FACTORIES:
        decline_percent = (prior_week - this_week) / prior_week * 100
        if decline_percent >= WEEK_OVER_WEEK_DECLINE_WARNING_PERCENT:
            breaches.append(
                {
                    "key": "NORTH_STAR_WEEK_OVER_WEEK_DECLINE",
                    "severity": "WARNING",
                    "detail": (
                        f"Weekly active factories dropped {round(decline_percent, 1)}% "
                        f"({prior_week} -> {this_week})"
                    ),
                }
            )

    return breaches
