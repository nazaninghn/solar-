"""
STEP 34.26: Data Pipeline API endpoints.

Serves energy data, KPIs, daily summaries, and data quality info.
"""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.modules.pipeline.kpi_engine import compute_kpis
from app.modules.pipeline.models import (
    DailyEnergySummary,
    DataQualityLog,
    MetricCatalog,
    Telemetry5m,
    TelemetryHourly,
)
from app.modules.pipeline.quality_engine import compute_data_quality_score
from app.modules.pipeline.schemas import (
    AggregationBucketResponse,
    DailyEnergySummaryResponse,
    DataQualityResponse,
    EnergyKPIResponse,
    MetricCatalogResponse,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/pipeline",
    tags=["Data Pipeline"],
)


@router.get("/metrics", response_model=list[MetricCatalogResponse])
def list_metric_catalog(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """34.6: List all registered metrics."""
    return db.query(MetricCatalog).filter(MetricCatalog.enabled == True).all()


@router.get("/energy/daily", response_model=list[DailyEnergySummaryResponse])
def get_daily_energy(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    """34.22: Get daily energy summaries."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    return (
        db.query(DailyEnergySummary)
        .filter(
            DailyEnergySummary.factory_id == factory.id,
            DailyEnergySummary.date >= cutoff,
        )
        .order_by(DailyEnergySummary.date.desc())
        .all()
    )


@router.get("/energy/kpi", response_model=EnergyKPIResponse)
def get_energy_kpis(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """34.23: Get today's energy KPIs."""
    today_str = date.today().isoformat()
    summary = (
        db.query(DailyEnergySummary)
        .filter(
            DailyEnergySummary.factory_id == factory.id,
            DailyEnergySummary.date == today_str,
        )
        .first()
    )

    if not summary:
        # Return zeros if no data yet
        return EnergyKPIResponse(
            solar_coverage=0.0,
            grid_dependency=1.0,
            battery_utilization=0.0,
            peak_demand_kw=0.0,
            total_savings=0.0,
            export_revenue=0.0,
            data_quality_score=0,
        )

    return compute_kpis(summary)


@router.get("/data-quality", response_model=DataQualityResponse)
def get_data_quality(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """34.24: Get current data quality score."""
    today_str = date.today().isoformat()

    # Compute fresh score
    quality_log = compute_data_quality_score(db=db, factory_id=factory.id, date_str=today_str)
    db.add(quality_log)
    db.commit()

    return DataQualityResponse(
        factory_id=factory.id,
        date=today_str,
        score=quality_log.score,
        completeness=quality_log.completeness,
        freshness=quality_log.freshness,
        validity=quality_log.validity,
        device_coverage=quality_log.device_coverage,
    )


@router.get("/aggregations/hourly", response_model=list[AggregationBucketResponse])
def get_hourly_aggregations(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    hours: int = Query(default=24, ge=1, le=168),
):
    """34.15: Get hourly aggregated data."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        db.query(TelemetryHourly)
        .filter(
            TelemetryHourly.factory_id == factory.id,
            TelemetryHourly.bucket_start >= cutoff,
        )
        .order_by(TelemetryHourly.bucket_start.desc())
        .limit(500)
        .all()
    )


@router.get("/aggregations/5m", response_model=list[AggregationBucketResponse])
def get_5m_aggregations(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    hours: int = Query(default=6, ge=1, le=24),
):
    """34.15: Get 5-minute aggregated data."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        db.query(Telemetry5m)
        .filter(
            Telemetry5m.factory_id == factory.id,
            Telemetry5m.bucket_start >= cutoff,
        )
        .order_by(Telemetry5m.bucket_start.desc())
        .limit(500)
        .all()
    )
