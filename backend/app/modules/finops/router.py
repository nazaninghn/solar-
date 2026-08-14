"""STEP 78: FinOps & Cost Optimization API — SUPER_ADMIN only, same
reasoning as app/modules/compliance/router.py: cost data spans every
organization, it isn't any one company's own data to see."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.modules.finops.schemas import (
    BudgetThresholdCreate,
    BudgetThresholdResponse,
    CostAttributionResponse,
    InfrastructureCostCreate,
    InfrastructureCostResponse,
    StorageReportResponse,
    TableStorageEntry,
)
from app.modules.finops.service import (
    compute_cost_per_organization,
    create_budget_threshold,
    create_infrastructure_cost,
    get_total_monthly_cost_usd,
    list_active_infrastructure_costs,
    list_budget_thresholds,
)
from app.modules.finops.storage import get_table_sizes_bytes, get_total_database_size_bytes

router = APIRouter(prefix="/api/v1/finops", tags=["FinOps & Cost Optimization"])


def _require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Platform admin access required.")
    return current_user


@router.get("/costs", response_model=list[InfrastructureCostResponse])
def list_costs_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return list_active_infrastructure_costs(db)


@router.post("/costs", response_model=InfrastructureCostResponse, status_code=201)
def create_cost_endpoint(
    data: InfrastructureCostCreate,
    admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return create_infrastructure_cost(
        db, data.name, data.category, data.monthly_cost_usd, admin, data.notes, data.effective_from
    )


@router.get("/cost-attribution", response_model=CostAttributionResponse)
def cost_attribution_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    return CostAttributionResponse(
        total_monthly_cost_usd=get_total_monthly_cost_usd(db),
        window_days=days,
        organizations=compute_cost_per_organization(db, days),
    )


@router.get("/budgets", response_model=list[BudgetThresholdResponse])
def list_budgets_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return list_budget_thresholds(db)


@router.post("/budgets", response_model=BudgetThresholdResponse, status_code=201)
def create_budget_endpoint(
    data: BudgetThresholdCreate,
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return create_budget_threshold(db, data.name, data.monthly_budget_usd, data.warning_percent)


@router.get("/storage", response_model=StorageReportResponse)
def storage_report_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    """78: storage optimization made data-driven — real
    pg_total_relation_size() per high-volume table (app.modules.finops.
    storage) instead of a retention policy doc with no numbers behind
    it."""
    sizes = get_table_sizes_bytes(db)
    total_high_volume = sum(sizes.values())
    database_total = get_total_database_size_bytes(db)
    capacity_bytes = settings.DATABASE_STORAGE_CAPACITY_GB * 1024**3

    return StorageReportResponse(
        tables=[
            TableStorageEntry(table_name=name, size_bytes=size, size_mb=round(size / 1024 / 1024, 2))
            for name, size in sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)
        ],
        total_high_volume_bytes=total_high_volume,
        database_total_bytes=database_total,
        capacity_gb=settings.DATABASE_STORAGE_CAPACITY_GB,
        percent_of_capacity=round((database_total / capacity_bytes) * 100, 2) if capacity_bytes else 0.0,
    )
