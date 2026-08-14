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
    """Get or create default quota for organization."""
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


def enforce_factory_quota(db: Session, organization_id: int) -> None:
    """Check if org can create another factory."""
    quota = get_quota(db, organization_id)
    current = db.query(Factory).filter(Factory.organization_id == organization_id).count()
    if current >= quota.max_factories:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Factory limit reached ({quota.max_factories}). Upgrade plan for more.",
        )


def enforce_device_quota(db: Session, organization_id: int) -> None:
    """Check if org can create another device."""
    quota = get_quota(db, organization_id)
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
    quota = get_quota(db, organization_id)
    current = db.query(User).filter(User.organization_id == organization_id).count()
    if current >= quota.max_users:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"User limit reached ({quota.max_users}). Upgrade plan for more.",
        )
