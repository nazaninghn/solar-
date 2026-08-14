"""
STEP 35.22: Forecast API Router.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.modules.forecasting.accuracy import compute_accuracy_metrics
from app.modules.forecasting.engine import (
    generate_load_forecast,
    generate_net_energy_forecast,
    generate_solar_forecast,
)
from app.modules.forecasting.models import (
    FORECAST_LOAD,
    FORECAST_NET_ENERGY,
    FORECAST_SOLAR,
    Forecast,
    ForecastPoint,
)
from app.modules.forecasting.schemas import (
    ForecastAccuracyResponse,
    ForecastPointResponse,
    ForecastResponse,
    ForecastSummaryResponse,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/forecast",
    tags=["Forecasting"],
)


def _build_response(db: Session, forecast: Forecast) -> ForecastResponse:
    """Load points and build full response."""
    points = (
        db.query(ForecastPoint)
        .filter(ForecastPoint.forecast_id == forecast.id)
        .order_by(ForecastPoint.timestamp.asc())
        .all()
    )
    return ForecastResponse(
        id=forecast.id,
        factory_id=forecast.factory_id,
        type=forecast.type,
        model_version=forecast.model_version,
        resolution=forecast.resolution,
        confidence=forecast.confidence,
        generated_at=forecast.generated_at,
        forecast_start=forecast.forecast_start,
        forecast_end=forecast.forecast_end,
        status=forecast.status,
        points=[ForecastPointResponse.model_validate(p) for p in points],
    )


@router.get("", response_model=ForecastSummaryResponse)
def get_forecast_summary(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """Quick forecast summary for dashboard."""
    solar_fc = (
        db.query(Forecast)
        .filter(Forecast.factory_id == factory.id, Forecast.type == FORECAST_SOLAR)
        .order_by(Forecast.generated_at.desc())
        .first()
    )
    load_fc = (
        db.query(Forecast)
        .filter(Forecast.factory_id == factory.id, Forecast.type == FORECAST_LOAD)
        .order_by(Forecast.generated_at.desc())
        .first()
    )

    solar_kwh = 0.0
    load_kwh = 0.0
    confidence = 0.8
    model_version = "none"
    generated_at = None

    if solar_fc:
        points = db.query(ForecastPoint).filter(ForecastPoint.forecast_id == solar_fc.id).all()
        solar_kwh = sum(p.predicted_value for p in points)
        confidence = solar_fc.confidence
        model_version = solar_fc.model_version
        generated_at = solar_fc.generated_at

    if load_fc:
        points = db.query(ForecastPoint).filter(ForecastPoint.forecast_id == load_fc.id).all()
        load_kwh = sum(p.predicted_value for p in points)

    return ForecastSummaryResponse(
        solar_forecast_kwh=round(solar_kwh, 1),
        load_forecast_kwh=round(load_kwh, 1),
        net_energy_kwh=round(solar_kwh - load_kwh, 1),
        confidence=confidence,
        model_version=model_version,
        generated_at=generated_at,
    )


@router.get("/solar", response_model=ForecastResponse)
def get_solar_forecast(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    hours: int = Query(default=24, ge=1, le=168),
    regenerate: bool = Query(default=False),
):
    """35.8: Get or generate solar forecast."""
    if not regenerate:
        existing = (
            db.query(Forecast)
            .filter(Forecast.factory_id == factory.id, Forecast.type == FORECAST_SOLAR)
            .order_by(Forecast.generated_at.desc())
            .first()
        )
        if existing:
            return _build_response(db, existing)

    forecast = generate_solar_forecast(db=db, factory_id=factory.id, hours_ahead=hours)
    return _build_response(db, forecast)


@router.get("/load", response_model=ForecastResponse)
def get_load_forecast(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    hours: int = Query(default=24, ge=1, le=168),
    regenerate: bool = Query(default=False),
):
    """35.9: Get or generate load forecast."""
    if not regenerate:
        existing = (
            db.query(Forecast)
            .filter(Forecast.factory_id == factory.id, Forecast.type == FORECAST_LOAD)
            .order_by(Forecast.generated_at.desc())
            .first()
        )
        if existing:
            return _build_response(db, existing)

    forecast = generate_load_forecast(db=db, factory_id=factory.id, hours_ahead=hours)
    return _build_response(db, forecast)


@router.get("/net-energy", response_model=ForecastResponse)
def get_net_energy_forecast(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    hours: int = Query(default=24, ge=1, le=168),
):
    """35.16: Net energy = solar - load."""
    forecast = generate_net_energy_forecast(db=db, factory_id=factory.id, hours_ahead=hours)
    return _build_response(db, forecast)


@router.get("/accuracy", response_model=list[ForecastAccuracyResponse])
def get_forecast_accuracy(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """35.17: Get forecast accuracy metrics."""
    results = []
    for fc_type in [FORECAST_SOLAR, FORECAST_LOAD, FORECAST_NET_ENERGY]:
        metrics = compute_accuracy_metrics(db=db, factory_id=factory.id, forecast_type=fc_type)
        if metrics.sample_count > 0:
            results.append(metrics)
    return results
