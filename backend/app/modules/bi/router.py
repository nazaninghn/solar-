"""STEP 80: Business Intelligence & KPI API — SUPER_ADMIN only, same
reasoning as app/modules/finops and app/modules/compliance: this data
spans every organization, it isn't any one company's own data."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.modules.bi.funnel import compute_activation_rate, compute_funnel, compute_signups
from app.modules.bi.retention import compute_cohort_retention, compute_weekly_active_factories
from app.modules.bi.revenue import compute_arr, compute_ltv, compute_mrr, compute_revenue_churn
from app.modules.bi.schemas import (
    ActivationRateResponse,
    BiDashboardResponse,
    CohortResponse,
    FunnelStage,
    NorthStarResponse,
    RevenueResponse,
    SegmentationResponse,
    SignupDay,
)
from app.modules.bi.segmentation import segment_by_industry, segment_by_plan, segment_by_size

router = APIRouter(prefix="/api/v1/bi", tags=["Business Intelligence"])


def _require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Platform admin access required.")
    return current_user


@router.get("/north-star", response_model=NorthStarResponse)
def north_star_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return NorthStarResponse(**compute_weekly_active_factories(db))


@router.get("/signups", response_model=list[SignupDay])
def signups_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    return [SignupDay(**row) for row in compute_signups(db, days)]


@router.get("/activation", response_model=ActivationRateResponse)
def activation_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    return ActivationRateResponse(**compute_activation_rate(db, days))


@router.get("/funnel", response_model=list[FunnelStage])
def funnel_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    return [FunnelStage(**stage) for stage in compute_funnel(db, days)]


@router.get("/cohorts", response_model=list[CohortResponse])
def cohorts_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
    months: int = Query(default=6, ge=1, le=24),
):
    return compute_cohort_retention(db, months)


@router.get("/revenue", response_model=RevenueResponse)
def revenue_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return RevenueResponse(
        mrr=compute_mrr(db),
        arr=compute_arr(db),
        churn=compute_revenue_churn(db),
        ltv=compute_ltv(db),
    )


@router.get("/segmentation", response_model=SegmentationResponse)
def segmentation_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return SegmentationResponse(
        by_plan=segment_by_plan(db),
        by_industry=segment_by_industry(db),
        by_size=segment_by_size(db),
    )


@router.get("/dashboard", response_model=BiDashboardResponse)
def dashboard_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    """80: one call for everything docs/bi/metric-dictionary.md
    defines — the same "one dashboard call" pattern as /api/v1/admin/
    dashboard and /api/v1/finops/cost-attribution."""
    signups = compute_signups(db, days=30)

    return BiDashboardResponse(
        north_star=NorthStarResponse(**compute_weekly_active_factories(db)),
        signups_last_30_days=sum(s["signups"] for s in signups),
        activation=ActivationRateResponse(**compute_activation_rate(db, days=30)),
        funnel=[FunnelStage(**stage) for stage in compute_funnel(db, days=30)],
        revenue=RevenueResponse(
            mrr=compute_mrr(db),
            arr=compute_arr(db),
            churn=compute_revenue_churn(db),
            ltv=compute_ltv(db),
        ),
        segmentation=SegmentationResponse(
            by_plan=segment_by_plan(db),
            by_industry=segment_by_industry(db),
            by_size=segment_by_size(db),
        ),
    )
