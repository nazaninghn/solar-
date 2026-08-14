"""
STEP 80: revenue metrics — real formulas against Subscription/Plan/
Payment, the way they'll actually compute once a real subscription
exists. As of this step, `subscriptions` has zero rows in this
deployment (confirmed: no job or endpoint has ever created one), so
every function here correctly returns 0/None today — that's the
correct answer for "no revenue has been recorded yet", not a
placeholder standing in for a number nobody computed.

CAC (Customer Acquisition Cost) is deliberately NOT implemented here —
it needs marketing/ad spend data, and nothing in this codebase tracks
that at all. Fabricating a CAC formula against non-existent spend data
would be worse than not having one.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.billing.models import Plan, Subscription


def _monthly_equivalent_price(subscription: Subscription, plan: Plan) -> float:
    if subscription.billing_cycle == "ANNUAL" and plan.annual_price is not None:
        return plan.annual_price / 12
    return plan.monthly_price


def compute_mrr(db: Session) -> float:
    rows = db.execute(
        select(Subscription, Plan)
        .join(Plan, Plan.id == Subscription.plan_id)
        .where(Subscription.status == "ACTIVE")
    ).all()

    return round(sum(_monthly_equivalent_price(sub, plan) for sub, plan in rows), 2)


def compute_arr(db: Session) -> float:
    return round(compute_mrr(db) * 12, 2)


def compute_revenue_churn(db: Session, days: int = 30) -> dict:
    """
    No historical MRR snapshot exists (nothing has ever recorded "MRR
    as of date X"), so starting-period MRR is approximated as
    current MRR + MRR lost to cancellations in the window — the same
    "reconstruct from what we still have" approach used because there's
    no time-series to read it from directly. Exact once a real MRR
    snapshot table is worth adding (would need real subscription
    volume to justify).
    """
    window_start = datetime.now(timezone.utc) - timedelta(days=days)

    cancelled_rows = db.execute(
        select(Subscription, Plan)
        .join(Plan, Plan.id == Subscription.plan_id)
        .where(Subscription.cancelled_at >= window_start)
    ).all()

    cancelled_mrr = sum(_monthly_equivalent_price(sub, plan) for sub, plan in cancelled_rows)
    current_mrr = compute_mrr(db)
    starting_mrr_estimate = current_mrr + cancelled_mrr

    churn_rate_percent = (
        round(cancelled_mrr / starting_mrr_estimate * 100, 2) if starting_mrr_estimate > 0 else 0.0
    )

    return {
        "window_days": days,
        "cancelled_mrr": round(cancelled_mrr, 2),
        "current_mrr": current_mrr,
        "churn_rate_percent": churn_rate_percent,
    }


def compute_ltv(db: Session) -> dict:
    """LTV = average monthly revenue per active org / monthly churn
    rate. Undefined (None) rather than infinite when churn is exactly
    0% — a 0% churn rate over a 30-day sample doesn't mean customers
    never leave, it means none happened to in this window, and
    reporting "infinite lifetime value" would be actively misleading."""
    active_org_count = len(
        db.scalars(select(Subscription.organization_id).where(Subscription.status == "ACTIVE")).all()
    )
    mrr = compute_mrr(db)
    avg_revenue_per_org = round(mrr / active_org_count, 2) if active_org_count else 0.0

    churn = compute_revenue_churn(db)
    monthly_churn_rate = churn["churn_rate_percent"] / 100

    ltv = round(avg_revenue_per_org / monthly_churn_rate, 2) if monthly_churn_rate > 0 else None

    return {
        "active_organizations": active_org_count,
        "avg_monthly_revenue_per_org": avg_revenue_per_org,
        "monthly_churn_rate_percent": churn["churn_rate_percent"],
        "estimated_ltv": ltv,
    }
