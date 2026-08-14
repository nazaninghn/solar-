"""STEP 80: organization segmentation — by plan tier, industry, and
size, all computed from real columns already in the schema."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.factory import Factory
from app.models.organization import Organization
from app.modules.billing.models import Plan, Subscription


def segment_by_plan(db: Session) -> list[dict]:
    rows = db.execute(
        select(Plan.name, func.count(Subscription.id))
        .select_from(Subscription)
        .join(Plan, Plan.id == Subscription.plan_id)
        .where(Subscription.status == "ACTIVE")
        .group_by(Plan.name)
    ).all()

    subscribed_org_count = sum(count for _, count in rows)
    total_org_count = db.scalar(select(func.count(Organization.id))) or 0
    unsubscribed = total_org_count - subscribed_org_count

    result = [{"plan": name, "organization_count": count} for name, count in rows]
    if unsubscribed > 0:
        result.append({"plan": "NO_SUBSCRIPTION", "organization_count": unsubscribed})

    return result


def segment_by_industry(db: Session) -> list[dict]:
    rows = db.execute(
        select(Factory.industry, func.count(Factory.id))
        .group_by(Factory.industry)
        .order_by(func.count(Factory.id).desc())
    ).all()

    return [
        {"industry": industry or "UNSPECIFIED", "factory_count": count} for industry, count in rows
    ]


def segment_by_size(db: Session) -> list[dict]:
    """Buckets an organization by its factory count — a simple,
    defensible proxy for account size given nothing tracks employee
    count or revenue-tier independent of the SaaS plan itself."""
    rows = db.execute(
        select(Organization.id, func.count(Factory.id))
        .select_from(Organization)
        .outerjoin(Factory, Factory.organization_id == Organization.id)
        .group_by(Organization.id)
    ).all()

    buckets = {"0_factories": 0, "1_factory": 0, "2_to_5_factories": 0, "6_plus_factories": 0}
    for _, factory_count in rows:
        if factory_count == 0:
            buckets["0_factories"] += 1
        elif factory_count == 1:
            buckets["1_factory"] += 1
        elif factory_count <= 5:
            buckets["2_to_5_factories"] += 1
        else:
            buckets["6_plus_factories"] += 1

    return [{"bucket": bucket, "organization_count": count} for bucket, count in buckets.items()]
