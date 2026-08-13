from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    BackfillRequest,
    BackfillResponse,
    DailyEnergyResponse,
    HourlyEnergyResponse,
    MonthlyEnergyResponse,
)
from app.analytics.service import (
    backfill_analytics,
    get_daily_analytics,
    get_hourly_analytics,
    get_monthly_analytics,
    get_today_analytics,
)
from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/analytics",
    tags=["Analytics"],
)


@router.get("/today", response_model=DailyEnergyResponse)
def analytics_today(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    result = get_today_analytics(db=db, factory_id=factory.id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No energy data recorded yet today",
        )

    return result


@router.get("/hourly", response_model=list[HourlyEnergyResponse])
def analytics_hourly(
    date_: date = Query(default=None, alias="date"),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    if date_ is None:
        date_ = datetime.now(timezone.utc).date()

    return get_hourly_analytics(db=db, factory_id=factory.id, day=date_)


@router.get("/daily", response_model=list[DailyEnergyResponse])
def analytics_daily(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=30, le=366),
    offset: int = Query(default=0, ge=0),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    if end_date is None:
        end_date = datetime.now(timezone.utc).date()
    if start_date is None:
        start_date = end_date - timedelta(days=7)

    return get_daily_analytics(
        db=db,
        factory_id=factory.id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@router.get("/monthly", response_model=list[MonthlyEnergyResponse])
def analytics_monthly(
    limit: int = Query(default=12, le=60),
    offset: int = Query(default=0, ge=0),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    rows = get_monthly_analytics(
        db=db, factory_id=factory.id, limit=limit, offset=offset
    )

    return [
        {
            "factory_id": row.factory_id,
            "month": row.month,
            "solar_generation_kwh": row.solar_kwh,
            "factory_consumption_kwh": row.consumption_kwh,
            "grid_import_kwh": row.grid_import_kwh,
            "grid_export_kwh": row.grid_export_kwh,
            "total_savings": row.total_savings,
            "total_revenue": row.total_revenue,
            "data_completeness": row.data_completeness,
        }
        for row in rows
    ]


@router.post("/backfill", response_model=BackfillResponse)
def analytics_backfill(
    data: BackfillRequest,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return backfill_analytics(
        db=db, factory_id=factory.id, start=data.start, end=data.end
    )
