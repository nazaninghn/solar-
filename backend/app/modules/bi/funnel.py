"""
STEP 80: acquisition & activation funnel — real computation against
organizations/factories/devices/recommendations' own created_at
columns, nothing fabricated or simulated. See docs/bi/metric-
dictionary.md for what each of these means and why.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.factory import Factory
from app.models.organization import Organization
from app.models.recommendation import Recommendation

ACTIVATION_WINDOW_DAYS = 7


def compute_signups(db: Session, days: int = 30) -> list[dict]:
    """Organizations created per day over the window — signups are
    counted at the organization level (one signup = one new company),
    matching how registration actually works (app.modules.auth.service.
    register_user always creates exactly one new Organization)."""
    window_start = datetime.now(timezone.utc) - timedelta(days=days)

    rows = db.execute(
        select(
            func.date(Organization.created_at).label("day"),
            func.count(Organization.id),
        )
        .where(Organization.created_at >= window_start)
        .group_by(func.date(Organization.created_at))
        .order_by(func.date(Organization.created_at))
    ).all()

    return [{"date": row.day.isoformat(), "signups": row[1]} for row in rows]


def compute_activation_rate(
    db: Session, days: int = 30, activation_window_days: int = ACTIVATION_WINDOW_DAYS
) -> dict:
    """% of organizations created in the window that created their
    first factory within activation_window_days of their OWN signup
    (not within the reporting window) — an org that signed up on day 1
    of a 30-day window and activated on day 5 counts as activated even
    though day 5 might fall inside a totally different reporting slice
    if measured the other way."""
    window_start = datetime.now(timezone.utc) - timedelta(days=days)

    cohort_orgs = db.execute(
        select(Organization.id, Organization.created_at).where(
            Organization.created_at >= window_start
        )
    ).all()

    if not cohort_orgs:
        return {"cohort_size": 0, "activated_count": 0, "activation_rate_percent": 0.0}

    org_ids = [row.id for row in cohort_orgs]
    signup_at = {row.id: row.created_at for row in cohort_orgs}

    first_factory_at = dict(
        db.execute(
            select(Factory.organization_id, func.min(Factory.created_at))
            .where(Factory.organization_id.in_(org_ids))
            .group_by(Factory.organization_id)
        ).all()
    )

    activated_count = 0
    for org_id in org_ids:
        first_factory = first_factory_at.get(org_id)
        if first_factory is None:
            continue
        if (first_factory - signup_at[org_id]) <= timedelta(days=activation_window_days):
            activated_count += 1

    return {
        "cohort_size": len(org_ids),
        "activated_count": activated_count,
        "activation_rate_percent": round(activated_count / len(org_ids) * 100, 1),
    }


def compute_funnel(db: Session, days: int = 30) -> list[dict]:
    """Stage counts for organizations signed up within the window —
    each stage is "has this org EVER reached this stage", not
    "reached it within the window", so activation lag doesn't make
    later stages look artificially small for orgs that signed up near
    the end of the window."""
    window_start = datetime.now(timezone.utc) - timedelta(days=days)

    cohort_org_ids = set(
        db.scalars(select(Organization.id).where(Organization.created_at >= window_start))
    )
    cohort_size = len(cohort_org_ids)

    if cohort_size == 0:
        return [
            {"stage": "signed_up", "count": 0},
            {"stage": "created_factory", "count": 0},
            {"stage": "added_device", "count": 0},
            {"stage": "viewed_recommendation", "count": 0},
        ]

    factory_org_ids = set(
        db.scalars(
            select(Factory.organization_id).where(Factory.organization_id.in_(cohort_org_ids))
        )
    )

    org_factory_ids = set(
        db.scalars(
            select(Factory.id).where(Factory.organization_id.in_(cohort_org_ids))
        )
    )
    device_org_ids = (
        set(
            db.scalars(
                select(Factory.organization_id)
                .join(Device, Device.factory_id == Factory.id)
                .where(Factory.id.in_(org_factory_ids))
            )
        )
        if org_factory_ids
        else set()
    )

    recommendation_org_ids = (
        set(
            db.scalars(
                select(Factory.organization_id)
                .join(Recommendation, Recommendation.factory_id == Factory.id)
                .where(Factory.id.in_(org_factory_ids))
            )
        )
        if org_factory_ids
        else set()
    )

    return [
        {"stage": "signed_up", "count": cohort_size},
        {"stage": "created_factory", "count": len(factory_org_ids)},
        {"stage": "added_device", "count": len(device_org_ids)},
        {"stage": "viewed_recommendation", "count": len(recommendation_org_ids)},
    ]
