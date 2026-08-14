"""STEP 51: Performance & Capacity API (Admin)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.modules.performance.models import (
    CapacityMetric,
    CircuitBreakerState,
    PerformanceBudget,
    TenantQuota,
)

router = APIRouter(prefix="/api/v1/admin/performance", tags=["Performance"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    from fastapi import HTTPException
    if current_user.role not in ("SUPER_ADMIN", "COMPANY_ADMIN"):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@router.get("/capacity")
def list_capacity_metrics(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """51.51: Current capacity metrics."""
    return db.query(CapacityMetric).order_by(CapacityMetric.measured_at.desc()).limit(20).all()


@router.get("/budgets")
def list_performance_budgets(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """51.52: Performance budget targets."""
    return db.query(PerformanceBudget).filter(PerformanceBudget.enabled == True).all()


@router.get("/circuit-breakers")
def list_circuit_breakers(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """51.37: Circuit breaker states for external services."""
    return db.query(CircuitBreakerState).all()


@router.get("/quotas")
def list_quotas(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """51.59: Tenant quotas."""
    return db.query(TenantQuota).limit(50).all()


@router.get("/quotas/{organization_id}")
def get_org_quota(
    organization_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Get specific org quota."""
    from app.modules.performance.quota_enforcement import get_quota
    return get_quota(db, organization_id)
