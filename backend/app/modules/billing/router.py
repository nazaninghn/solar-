"""STEP 44.13/44.30: Billing & Settlement API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.billing.models import (
    Invoice,
    Payment,
    Plan,
    Settlement,
    Subscription,
    UsageRecord,
)
from app.modules.billing.schemas import (
    InvoiceResponse,
    PaymentResponse,
    PlanResponse,
    SettlementResponse,
    SubscriptionResponse,
    UsageResponse,
)

# Platform Billing
billing_router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])


@billing_router.get("/plans", response_model=list[PlanResponse])
def list_plans(db: Session = Depends(get_db)):
    return db.query(Plan).filter(Plan.active == True).all()


@billing_router.get("/subscription", response_model=SubscriptionResponse)
def get_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sub = db.query(Subscription).filter(Subscription.organization_id == current_user.organization_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription.")
    return sub


@billing_router.get("/invoices", response_model=list[InvoiceResponse])
def list_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Invoice)
        .filter(Invoice.organization_id == current_user.organization_id)
        .order_by(Invoice.created_at.desc())
        .limit(50)
        .all()
    )


@billing_router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id, Invoice.organization_id == current_user.organization_id
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return inv


@billing_router.get("/payments", response_model=list[PaymentResponse])
def list_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Payment)
        .filter(Payment.organization_id == current_user.organization_id)
        .order_by(Payment.created_at.desc())
        .limit(50)
        .all()
    )


@billing_router.get("/usage", response_model=list[UsageResponse])
def list_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(UsageRecord)
        .filter(UsageRecord.organization_id == current_user.organization_id)
        .order_by(UsageRecord.period_start.desc())
        .limit(50)
        .all()
    )


# Energy Settlement
settlement_router = APIRouter(prefix="/api/v1/factories/{factory_id}/settlements", tags=["Energy Settlement"])


@settlement_router.get("", response_model=list[SettlementResponse])
def list_settlements(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return (
        db.query(Settlement)
        .filter(Settlement.factory_id == factory.id)
        .order_by(Settlement.period_start.desc())
        .limit(24)
        .all()
    )


@settlement_router.get("/{settlement_id}", response_model=SettlementResponse)
def get_settlement(
    settlement_id: int,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    s = db.query(Settlement).filter(Settlement.id == settlement_id, Settlement.factory_id == factory.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Settlement not found.")
    return s
