"""
STEP 35.17-35.19: Forecast Accuracy Evaluation.

Compares forecast predictions with actual values.
Computes MAE, RMSE, MAPE, Bias.
"""

import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.forecasting.models import Forecast, ForecastAccuracy, ForecastPoint
from app.modules.forecasting.schemas import ForecastAccuracyResponse


def record_actual(
    db: Session,
    forecast_id: int,
    factory_id: int,
    timestamp: datetime,
    actual_value: float,
) -> ForecastAccuracy | None:
    """35.17: Record actual value and compute error for a forecast point."""
    point = (
        db.query(ForecastPoint)
        .filter(
            ForecastPoint.forecast_id == forecast_id,
            ForecastPoint.timestamp == timestamp,
        )
        .first()
    )
    if not point:
        return None

    error = point.predicted_value - actual_value
    abs_error = abs(error)

    record = ForecastAccuracy(
        forecast_id=forecast_id,
        factory_id=factory_id,
        timestamp=timestamp,
        predicted_value=point.predicted_value,
        actual_value=actual_value,
        error=round(error, 3),
        absolute_error=round(abs_error, 3),
        created_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    return record


def compute_accuracy_metrics(
    db: Session,
    factory_id: int,
    forecast_type: str,
    horizon: str = "24h",
) -> ForecastAccuracyResponse:
    """35.17-35.19: Compute aggregate accuracy metrics."""
    # Get recent accuracy records
    records = (
        db.query(ForecastAccuracy)
        .join(Forecast, ForecastAccuracy.forecast_id == Forecast.id)
        .filter(
            ForecastAccuracy.factory_id == factory_id,
            Forecast.type == forecast_type,
        )
        .order_by(ForecastAccuracy.created_at.desc())
        .limit(500)
        .all()
    )

    if not records:
        return ForecastAccuracyResponse(
            forecast_type=forecast_type,
            horizon=horizon,
            mae=0.0,
            rmse=0.0,
            mape=None,
            bias=0.0,
            sample_count=0,
        )

    n = len(records)
    errors = [r.error for r in records]
    abs_errors = [r.absolute_error for r in records]
    actuals = [r.actual_value for r in records]

    mae = sum(abs_errors) / n
    rmse = math.sqrt(sum(e ** 2 for e in errors) / n)
    bias = sum(errors) / n

    # MAPE (avoid division by zero)
    mape = None
    non_zero_actuals = [(ae, a) for ae, a in zip(abs_errors, actuals) if a != 0]
    if non_zero_actuals:
        mape = sum(ae / abs(a) for ae, a in non_zero_actuals) / len(non_zero_actuals) * 100

    return ForecastAccuracyResponse(
        forecast_type=forecast_type,
        horizon=horizon,
        mae=round(mae, 2),
        rmse=round(rmse, 2),
        mape=round(mape, 2) if mape is not None else None,
        bias=round(bias, 2),
        sample_count=n,
    )
