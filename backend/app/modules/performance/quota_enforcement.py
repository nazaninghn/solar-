"""
STEP 51.58-51.59: Tenant Quota Enforcement.

Prevents noisy neighbor issues by enforcing per-org resource limits.
"""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.factory import Factory
from app.models.user import User
from app.modules.performance.models import TenantQuota

logger = logging.getLogger(__name__)


def get_quota(db: Session, organization_id: int) -> TenantQuota:
    """Get or create default quota for organization. Read-only use
    (e.g. the admin display endpoint) - enforce_*_quota below uses its
    own locked variant, not this one."""
    quota = db.query(TenantQuota).filter(
        TenantQuota.organization_id == organization_id
    ).first()
    if not quota:
        quota = TenantQuota(
            organization_id=organization_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(quota)
        db.commit()
        db.refresh(quota)
    return quota


def _get_quota_locked(db: Session, organization_id: int) -> TenantQuota:
    """85: enforce_*_quota is a classic check-then-act pattern (COUNT,
    compare, and the caller's own db.commit() of the new row happen as
    separate statements) - with no lock, two concurrent requests can
    both read a count under the limit before either commits, letting
    an org exceed its plan's quota. SELECT ... FOR UPDATE on this org's
    TenantQuota row serializes concurrent enforce_*_quota calls for the
    SAME org (other orgs are unaffected) - the second request's lock
    acquisition blocks until the first's transaction commits (from the
    caller's own db.commit() after inserting the new row), so its COUNT
    then correctly sees the first request's insert.

    A real load test against a live server (10 and 30 concurrent
    factory-create requests against a quota of 5) didn't reproduce a
    violation even before this fix - Postgres's own transaction timing
    happened not to expose the window in that test. That's a negative
    result, not proof the race can't happen; the unlocked pattern is a
    genuine anti-pattern regardless, so it's hardened here rather than
    left as "probably fine in practice."
    """
    quota = (
        db.query(TenantQuota)
        .filter(TenantQuota.organization_id == organization_id)
        .with_for_update()
        .first()
    )
    if not quota:
        quota = TenantQuota(
            organization_id=organization_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(quota)
        db.commit()
        db.refresh(quota)
        # Re-select with the lock now that the row exists - the insert
        # above already implicitly holds it in this transaction, but
        # re-querying keeps this function's return value consistent
        # with the locked path below.
        quota = (
            db.query(TenantQuota)
            .filter(TenantQuota.organization_id == organization_id)
            .with_for_update()
            .first()
        )
    return quota


def enforce_factory_quota(db: Session, organization_id: int) -> None:
    """Check if org can create another factory."""
    quota = _get_quota_locked(db, organization_id)
    current = db.query(Factory).filter(Factory.organization_id == organization_id).count()
    if current >= quota.max_factories:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Factory limit reached ({quota.max_factories}). Upgrade plan for more.",
        )


def enforce_device_quota(db: Session, organization_id: int) -> None:
    """Check if org can create another device."""
    quota = _get_quota_locked(db, organization_id)
    factory_ids = [
        f.id for f in db.query(Factory.id).filter(Factory.organization_id == organization_id).all()
    ]
    current = db.query(Device).filter(Device.factory_id.in_(factory_ids)).count() if factory_ids else 0
    if current >= quota.max_devices:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Device limit reached ({quota.max_devices}). Upgrade plan for more.",
        )


def enforce_user_quota(db: Session, organization_id: int) -> None:
    """Check if org can add another user."""
    quota = _get_quota_locked(db, organization_id)
    current = db.query(User).filter(User.organization_id == organization_id).count()
    if current >= quota.max_users:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"User limit reached ({quota.max_users}). Upgrade plan for more.",
        )
