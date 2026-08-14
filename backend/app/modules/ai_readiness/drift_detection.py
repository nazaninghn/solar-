"""
STEP 81: Model Monitoring — forecast accuracy drift, computed from the
real ForecastAccuracy history the forecasting engine already writes
(app/modules/forecasting/accuracy.py's record_actual). No new
telemetry, just a trend comparison over what already exists.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.forecasting.models import Forecast, ForecastAccuracy

DRIFT_WINDOW_DAYS = 14
MIN_SAMPLES_PER_WINDOW = 10
# A model getting 25% worse isn't noise — 78/79's threshold-picking
# precedent (2.5 stddev for anomalies, 80% budget warning) applies the
# same way here: a documented, tunable default, not a proven number.
DRIFT_WARNING_THRESHOLD_PERCENT = 25.0


def _window_mae(db: Session, forecast_type: str, window_start: datetime, window_end: datetime) -> tuple[float | None, int]:
    records = db.scalars(
        select(ForecastAccuracy)
        .join(Forecast, ForecastAccuracy.forecast_id == Forecast.id)
        .where(
            Forecast.type == forecast_type,
            ForecastAccuracy.created_at >= window_start,
            ForecastAccuracy.created_at < window_end,
        )
    ).all()

    if not records:
        return None, 0

    mae = sum(r.absolute_error for r in records) / len(records)
    return round(mae, 3), len(records)


def detect_forecast_drift(db: Session, forecast_types: tuple[str, ...] = ("SOLAR_GENERATION", "LOAD")) -> list[dict]:
    now = datetime.now(timezone.utc)
    recent_start = now - timedelta(days=DRIFT_WINDOW_DAYS)
    prior_start = now - timedelta(days=DRIFT_WINDOW_DAYS * 2)

    results = []

    for forecast_type in forecast_types:
        recent_mae, recent_n = _window_mae(db, forecast_type, recent_start, now)
        prior_mae, prior_n = _window_mae(db, forecast_type, prior_start, recent_start)

        entry = {
            "forecast_type": forecast_type,
            "recent_mae": recent_mae,
            "recent_sample_count": recent_n,
            "prior_mae": prior_mae,
            "prior_sample_count": prior_n,
            "drift_percent": None,
            "drifted": False,
        }

        if (
            recent_n >= MIN_SAMPLES_PER_WINDOW
            and prior_n >= MIN_SAMPLES_PER_WINDOW
            and prior_mae
            and prior_mae > 0
        ):
            drift_percent = round((recent_mae - prior_mae) / prior_mae * 100, 1)
            entry["drift_percent"] = drift_percent
            entry["drifted"] = drift_percent >= DRIFT_WARNING_THRESHOLD_PERCENT

        results.append(entry)

    return results
