"""STEP 79: Compliance & Governance API — legal holds and vendor
governance. Platform-wide (SUPER_ADMIN only, same reasoning as
app/modules/admin/router.py's _require_platform_admin fix this same
step): a legal hold or vendor record isn't scoped to one organization's
own data, so a company's own admin has no business managing it."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.modules.compliance.schemas import (
    LegalHoldCreate,
    LegalHoldResponse,
    VendorCreate,
    VendorResponse,
)
from app.modules.compliance.service import (
    create_legal_hold,
    create_vendor,
    list_active_legal_holds,
    list_vendors,
    offboard_vendor,
    release_legal_hold,
)

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance & Governance"])


def _require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Platform admin access required.")
    return current_user


@router.get("/legal-holds", response_model=list[LegalHoldResponse])
def list_legal_holds_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return list_active_legal_holds(db)


@router.post("/legal-holds", response_model=LegalHoldResponse, status_code=201)
def create_legal_hold_endpoint(
    data: LegalHoldCreate,
    admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return create_legal_hold(db, data.resource_type, data.resource_id, data.reason, admin)


@router.post("/legal-holds/{hold_id}/release", response_model=LegalHoldResponse)
def release_legal_hold_endpoint(
    hold_id: int,
    admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    hold = release_legal_hold(db, hold_id, admin)
    if hold is None:
        raise HTTPException(status_code=404, detail="Legal hold not found or already released.")
    return hold


@router.get("/vendors", response_model=list[VendorResponse])
def list_vendors_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return list_vendors(db)


@router.post("/vendors", response_model=VendorResponse, status_code=201)
def create_vendor_endpoint(
    data: VendorCreate,
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return create_vendor(
        db,
        data.name,
        data.purpose,
        data.data_access_description,
        data.risk_tier,
        data.contract_reference,
        data.dpa_signed,
    )


@router.post("/vendors/{vendor_id}/offboard", response_model=VendorResponse)
def offboard_vendor_endpoint(
    vendor_id: int,
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    vendor = offboard_vendor(db, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found.")
    return vendor
