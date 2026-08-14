"""
STEP 35.8-35.12: Forecast Engine.

Orchestrates forecast generation: loads features, runs model, stores results.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.forecasting.models import (
    FC_READY,
    FORECAST_LOAD,
    FORECAST_NET_ENERGY,
    FORECAST_SOLAR,
    Forecast,
    ForecastPoint,
)
from app.modules.forecasting.models_ml.load_baseline import LoadBaselineModel
from app.modules.forecasting.models_ml.solar_baseline import SolarBaselineModel

logger = logging.getLogger(__name__)


def generate_solar_forecast(
    db: Session,
    factory_id: int,
    panel_capacity_kw: float = 500.0,
    cloud_forecast: dict[int, float] | None = None,
    hours_ahead: int = 24,
) -> Forecast:
    """35.8: Generate solar production forecast."""
    now = datetime.now(timezone.utc)
    timestamps = [now + timedelta(hours=h) for h in range(1, hours_ahead + 1)]

    model = SolarBaselineModel(
        panel_capacity_kw=panel_capacity_kw,
        cloud_forecast=cloud_forecast,
    )

    results = model.predict(features={"cloud_cover": 30}, timestamps=timestamps)

    # Calculate overall confidence
    avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0.8

    # Store forecast
    forecast = Forecast(
        factory_id=factory_id,
        type=FORECAST_SOLAR,
        model_version=model.version(),
        generated_at=now,
        forecast_start=timestamps[0],
        forecast_end=timestamps[-1],
        resolution="1h",
        confidence=round(avg_confidence, 3),
        status=FC_READY,
    )
    db.add(forecast)
    db.flush()  # Get ID

    # Store points
    for r in results:
        point = ForecastPoint(
            forecast_id=forecast.id,
            timestamp=r.timestamp,
            predicted_value=r.predicted_value,
            lower_bound=r.lower_bound,
            upper_bound=r.upper_bound,
            confidence=r.confidence,
            quality="GOOD",
        )
        db.add(point)

    db.commit()
    db.refresh(forecast)

    logger.info(
        f"Solar forecast generated for factory {factory_id}: {hours_ahead}h, "
        f"confidence={avg_confidence:.2f}, model={model.version()}",
        extra={"factory_id": factory_id},
    )
    return forecast


def generate_load_forecast(
    db: Session,
    factory_id: int,
    hours_ahead: int = 24,
) -> Forecast:
    """35.9: Generate factory load forecast."""
    now = datetime.now(timezone.utc)
    timestamps = [now + timedelta(hours=h) for h in range(1, hours_ahead + 1)]

    model = LoadBaselineModel()
    results = model.predict(features={}, timestamps=timestamps)

    avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0.9

    forecast = Forecast(
        factory_id=factory_id,
        type=FORECAST_LOAD,
        model_version=model.version(),
        generated_at=now,
        forecast_start=timestamps[0],
        forecast_end=timestamps[-1],
        resolution="1h",
        confidence=round(avg_confidence, 3),
        status=FC_READY,
    )
    db.add(forecast)
    db.flush()

    for r in results:
        point = ForecastPoint(
            forecast_id=forecast.id,
            timestamp=r.timestamp,
            predicted_value=r.predicted_value,
            lower_bound=r.lower_bound,
            upper_bound=r.upper_bound,
            confidence=r.confidence,
            quality="GOOD",
        )
        db.add(point)

    db.commit()
    db.refresh(forecast)

    logger.info(
        f"Load forecast generated for factory {factory_id}: {hours_ahead}h, "
        f"confidence={avg_confidence:.2f}",
        extra={"factory_id": factory_id},
    )
    return forecast


def generate_net_energy_forecast(
    db: Session,
    factory_id: int,
    hours_ahead: int = 24,
) -> Forecast:
    """35.16: Net Energy = Solar - Load."""
    now = datetime.now(timezone.utc)
    timestamps = [now + timedelta(hours=h) for h in range(1, hours_ahead + 1)]

    solar_model = SolarBaselineModel()
    load_model = LoadBaselineModel()

    solar_results = solar_model.predict(features={"cloud_cover": 30}, timestamps=timestamps)
    load_results = load_model.predict(features={}, timestamps=timestamps)

    forecast = Forecast(
        factory_id=factory_id,
        type=FORECAST_NET_ENERGY,
        model_version=f"net-{solar_model.version()}/{load_model.version()}",
        generated_at=now,
        forecast_start=timestamps[0],
        forecast_end=timestamps[-1],
        resolution="1h",
        confidence=0.8,
        status=FC_READY,
    )
    db.add(forecast)
    db.flush()

    for solar, load in zip(solar_results, load_results):
        net = solar.predicted_value - load.predicted_value
        lower = solar.lower_bound - load.upper_bound
        upper = solar.upper_bound - load.lower_bound
        confidence = min(solar.confidence, load.confidence)

        point = ForecastPoint(
            forecast_id=forecast.id,
            timestamp=solar.timestamp,
            predicted_value=round(net, 2),
            lower_bound=round(lower, 2),
            upper_bound=round(upper, 2),
            confidence=round(confidence, 3),
            quality="GOOD",
        )
        db.add(point)

    db.commit()
    db.refresh(forecast)
    return forecast
