from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User
from app.modules.admin.models import APIUsageMetric
from app.modules.finops.models import BudgetThreshold, InfrastructureCost


def create_infrastructure_cost(
    db: Session,
    name: str,
    category: str,
    monthly_cost_usd: float,
    created_by: User,
    notes: str | None = None,
    effective_from: date | None = None,
) -> InfrastructureCost:
    cost = InfrastructureCost(
        name=name,
        category=category,
        monthly_cost_usd=monthly_cost_usd,
        effective_from=effective_from or datetime.now(timezone.utc).date(),
        notes=notes,
        created_by=created_by.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)
    return cost


def list_active_infrastructure_costs(db: Session) -> list[InfrastructureCost]:
    today = datetime.now(timezone.utc).date()
    return db.scalars(
        select(InfrastructureCost).where(
            InfrastructureCost.effective_from <= today,
            (InfrastructureCost.effective_to.is_(None)) | (InfrastructureCost.effective_to >= today),
        )
    ).all()


def get_total_monthly_cost_usd(db: Session) -> float:
    return sum(c.monthly_cost_usd for c in list_active_infrastructure_costs(db))


def compute_cost_per_organization(db: Session, days: int = 30) -> list[dict]:
    """
    78: cost-per-customer, allocated by each organization's share of
    total API request volume over the window — the one usage signal
    actually measured per-organization (app.core.metrics.
    record_org_request -> APIUsageMetric). Storage isn't allocated
    this way since device_energy_readings etc. aren't partitioned by
    organization in a way this query can cheaply attribute per-org.

    Orgs with zero measured requests in the window get an equal split
    of whatever remains unattributed, rather than $0 — silence in the
    usage log isn't evidence of zero cost, it's evidence the flush job
    hasn't run yet or the org is new.
    """
    total_cost = get_total_monthly_cost_usd(db)
    window_start = datetime.now(timezone.utc) - timedelta(days=days)

    usage_by_org = dict(
        db.execute(
            select(APIUsageMetric.organization_id, func.sum(APIUsageMetric.request_count))
            .where(APIUsageMetric.period_start >= window_start)
            .group_by(APIUsageMetric.organization_id)
        ).all()
    )

    all_org_ids = set(db.scalars(select(Organization.id)).all())
    total_requests = sum(usage_by_org.values())

    results = []
    if total_requests > 0:
        for org_id in all_org_ids:
            requests = usage_by_org.get(org_id, 0)
            share = requests / total_requests
            results.append(
                {
                    "organization_id": org_id,
                    "request_count": requests,
                    "usage_share_percent": round(share * 100, 2),
                    "estimated_cost_usd": round(share * total_cost, 2),
                }
            )
    else:
        # No usage data at all yet — split evenly rather than claim
        # every organization costs nothing.
        equal_share = total_cost / len(all_org_ids) if all_org_ids else 0.0
        for org_id in all_org_ids:
            results.append(
                {
                    "organization_id": org_id,
                    "request_count": 0,
                    "usage_share_percent": round(100 / len(all_org_ids), 2) if all_org_ids else 0.0,
                    "estimated_cost_usd": round(equal_share, 2),
                }
            )

    return sorted(results, key=lambda r: r["estimated_cost_usd"], reverse=True)


# --- Budget thresholds ---


def create_budget_threshold(
    db: Session, name: str, monthly_budget_usd: float, warning_percent: float = 80.0
) -> BudgetThreshold:
    threshold = BudgetThreshold(
        name=name,
        monthly_budget_usd=monthly_budget_usd,
        warning_percent=warning_percent,
        created_at=datetime.now(timezone.utc),
    )
    db.add(threshold)
    db.commit()
    db.refresh(threshold)
    return threshold


def list_budget_thresholds(db: Session) -> list[BudgetThreshold]:
    return db.scalars(select(BudgetThreshold)).all()


def check_budget_thresholds(db: Session) -> list[dict]:
    """78: Budget Alerts — compares total known infra spend (78's own
    admin-entered InfrastructureCost rows) against each configured
    BudgetThreshold. Returns the thresholds currently breached (at or
    past warning_percent) so the caller (app.jobs.finops_jobs) can
    decide what to do about it — this function only computes, it
    doesn't alert."""
    total_cost = get_total_monthly_cost_usd(db)
    breaches = []

    for threshold in list_budget_thresholds(db):
        if threshold.monthly_budget_usd <= 0:
            continue

        percent_used = (total_cost / threshold.monthly_budget_usd) * 100
        if percent_used >= threshold.warning_percent:
            breaches.append(
                {
                    "threshold_id": threshold.id,
                    "name": threshold.name,
                    "monthly_budget_usd": threshold.monthly_budget_usd,
                    "current_cost_usd": total_cost,
                    "percent_used": round(percent_used, 1),
                    "severity": "CRITICAL" if percent_used >= 100 else "WARNING",
                }
            )

    return breaches
