from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.modules.compliance.models import (
    HOLD_RESOURCE_TYPE_ORGANIZATION,
    LegalHold,
    Vendor,
)


def is_organization_on_hold(db: Session, organization_id: int) -> bool:
    """79.33: checked before any retention purge or account deletion
    that would remove an organization's data."""
    return (
        db.scalar(
            select(LegalHold.id).where(
                LegalHold.resource_type == HOLD_RESOURCE_TYPE_ORGANIZATION,
                LegalHold.resource_id == organization_id,
                LegalHold.released_at.is_(None),
            )
        )
        is not None
    )


def get_held_organization_ids(db: Session) -> set[int]:
    """Used by retention_jobs.py to exclude held organizations' data
    from a purge query without checking hold status row-by-row."""
    rows = db.scalars(
        select(LegalHold.resource_id).where(
            LegalHold.resource_type == HOLD_RESOURCE_TYPE_ORGANIZATION,
            LegalHold.released_at.is_(None),
        )
    ).all()
    return set(rows)


def create_legal_hold(
    db: Session, resource_type: str, resource_id: int, reason: str, created_by: User
) -> LegalHold:
    hold = LegalHold(
        resource_type=resource_type,
        resource_id=resource_id,
        reason=reason,
        created_by=created_by.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(hold)
    db.commit()
    db.refresh(hold)
    return hold


def release_legal_hold(db: Session, hold_id: int, released_by: User) -> LegalHold | None:
    hold = db.get(LegalHold, hold_id)
    if hold is None or hold.released_at is not None:
        return None

    hold.released_at = datetime.now(timezone.utc)
    hold.released_by = released_by.id
    db.commit()
    db.refresh(hold)
    return hold


def list_active_legal_holds(db: Session) -> list[LegalHold]:
    return db.scalars(
        select(LegalHold).where(LegalHold.released_at.is_(None)).order_by(LegalHold.created_at.desc())
    ).all()


# --- Vendor governance (79.41-79.44) ---


def list_vendors(db: Session) -> list[Vendor]:
    return db.scalars(select(Vendor).order_by(Vendor.name)).all()


def create_vendor(
    db: Session,
    name: str,
    purpose: str,
    data_access_description: str,
    risk_tier: str,
    contract_reference: str | None = None,
    dpa_signed: bool = False,
) -> Vendor:
    vendor = Vendor(
        name=name,
        purpose=purpose,
        data_access_description=data_access_description,
        risk_tier=risk_tier,
        contract_reference=contract_reference,
        dpa_signed=dpa_signed,
        created_at=datetime.now(timezone.utc),
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


def offboard_vendor(db: Session, vendor_id: int) -> Vendor | None:
    """79.44: Vendor Offboarding — revoke/return/rotate are operational
    steps outside this codebase's control (a vendor's own systems); what
    this can track is the governance record itself moving to OFFBOARDED
    so it stops appearing as an active third-party data recipient."""
    vendor = db.get(Vendor, vendor_id)
    if vendor is None:
        return None

    vendor.status = "OFFBOARDED"
    vendor.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(vendor)
    return vendor
