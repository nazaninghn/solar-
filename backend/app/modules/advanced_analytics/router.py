"""STEP 45.54: Advanced Analytics API."""

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.modules.advanced_analytics.anomaly_detection import detect_solar_anomaly
from app.modules.advanced_analytics.forecast_evaluation import evaluate_forecast_accuracy
from app.modules.advanced_analytics.kpi_engine import compute_energy_kpis
from app.modules.advanced_analytics.models import (
    Anomaly,
    DailyEnergyMetric,
    DevicePerformance,
    EnergyKPI,
    RecommendationImpact,
)
from app.modules.advanced_analytics.schemas import (
    AnalyticsOverviewResponse,
    AnomalyResponse,
    DevicePerformanceResponse,
    EnergyKPIResponse,
    ForecastAccuracyMetrics,
    SavingsAttributionResponse,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/analytics",
    tags=["Advanced Analytics"],
)


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def analytics_overview(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """45.54: High-level analytics overview."""
    today = date.today().isoformat()
    daily = db.query(DailyEnergyMetric).filter(
        DailyEnergyMetric.factory_id == factory.id, DailyEnergyMetric.date == today
    ).first()

    anomaly_count = db.query(Anomaly).filter(
        Anomaly.factory_id == factory.id, Anomaly.status == "DETECTED"
    ).count()

    return AnalyticsOverviewResponse(
        factory_id=factory.id,
        period="today",
        solar_kwh=daily.solar_generation_kwh if daily else 0,
        consumption_kwh=daily.consumption_kwh if daily else 0,
        grid_import_kwh=daily.grid_import_kwh if daily else 0,
        grid_export_kwh=daily.grid_export_kwh if daily else 0,
        solar_coverage_pct=(daily.solar_coverage_rate or 0) * 100 if daily else 0,
        grid_dependency_pct=((daily.grid_import_kwh / daily.consumption_kwh) * 100) if daily and daily.consumption_kwh > 0 else 100,
        peak_demand_kw=daily.peak_demand_kw or 0 if daily else 0,
        total_savings=0,
        forecast_accuracy_pct=0,
        anomaly_count=anomaly_count,
        data_freshness="LIVE",
    )


@router.get("/kpis", response_model=EnergyKPIResponse)
def get_kpis(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365),
):
    """45.4: Energy KPIs for period."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    kpi = compute_energy_kpis(db, factory.id, start, now)
    return kpi


@router.get("/forecast-accuracy", response_model=list[ForecastAccuracyMetrics])
def forecast_accuracy(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """45.23: Forecast accuracy metrics."""
    results = []
    for ft in ["SOLAR_GENERATION", "FACTORY_CONSUMPTION", "GRID_PRICE"]:
        metrics = evaluate_forecast_accuracy(db, factory.id, ft)
        if metrics.sample_count > 0:
            results.append(metrics)
    return results


@router.get("/anomalies", response_model=list[AnomalyResponse])
def list_anomalies(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
):
    """45.32: List detected anomalies."""
    query = db.query(Anomaly).filter(Anomaly.factory_id == factory.id)
    if status:
        query = query.filter(Anomaly.status == status)
    return query.order_by(Anomaly.detected_at.desc()).limit(50).all()


@router.get("/device-performance", response_model=list[DevicePerformanceResponse])
def device_performance(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """45.33: Device performance metrics."""
    from app.models.device import Device
    device_ids = [d.id for d in db.query(Device.id).filter(Device.factory_id == factory.id).all()]
    if not device_ids:
        return []
    return (
        db.query(DevicePerformance)
        .filter(DevicePerformance.device_id.in_(device_ids))
        .order_by(DevicePerformance.period_start.desc())
        .limit(50)
        .all()
    )


@router.get("/savings", response_model=SavingsAttributionResponse)
def savings_attribution(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """45.49: Savings breakdown."""
    impacts = (
        db.query(RecommendationImpact)
        .filter(RecommendationImpact.factory_id == factory.id)
        .order_by(RecommendationImpact.created_at.desc())
        .limit(30)
        .all()
    )
    total_realized = sum(i.realized_saving or 0 for i in impacts)

    return SavingsAttributionResponse(
        solar_self_consumption=total_realized * 0.5,
        battery_arbitrage=total_realized * 0.2,
        load_shifting=total_realized * 0.1,
        peak_reduction=total_realized * 0.1,
        grid_export=total_realized * 0.05,
        optimization_recommendations=total_realized * 0.05,
        total=total_realized,
        currency="EUR",
    )
