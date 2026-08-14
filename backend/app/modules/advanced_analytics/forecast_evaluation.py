"""
STEP 45.16-45.22: Forecast Evaluation Engine.

Computes MAE, RMSE, MAPE, Bias from forecast vs actual records.
"""

import math
from sqlalchemy.orm import Session

from app.modules.advanced_analytics.models import ForecastRecord
from app.modules.advanced_analytics.schemas import ForecastAccuracyMetrics


def evaluate_forecast_accuracy(
    db: Session,
    factory_id: int,
    forecast_type: str,
    limit: int = 500,
) -> ForecastAccuracyMetrics:
    """Compute accuracy metrics from stored forecast records."""
    records = (
        db.query(ForecastRecord)
        .filter(
            ForecastRecord.factory_id == factory_id,
            ForecastRecord.forecast_type == forecast_type,
            ForecastRecord.actual_value != None,
        )
        .order_by(ForecastRecord.target_timestamp.desc())
        .limit(limit)
        .all()
    )

    if not records:
        return ForecastAccuracyMetrics(
            forecast_type=forecast_type, mae=0, rmse=0, mape=None, bias=0,
            sample_count=0, model_version="none",
        )

    n = len(records)
    errors = [r.actual_value - r.predicted_value for r in records]
    abs_errors = [abs(e) for e in errors]
    sq_errors = [e ** 2 for e in errors]

    mae = sum(abs_errors) / n
    rmse = math.sqrt(sum(sq_errors) / n)
    bias = sum(errors) / n

    # MAPE (exclude near-zero actuals)
    mape_items = [(abs(r.actual_value - r.predicted_value) / abs(r.actual_value))
                  for r in records if r.actual_value and abs(r.actual_value) > 1]
    mape = (sum(mape_items) / len(mape_items) * 100) if mape_items else None

    model_version = records[0].model_version if records else "unknown"

    return ForecastAccuracyMetrics(
        forecast_type=forecast_type,
        mae=round(mae, 2),
        rmse=round(rmse, 2),
        mape=round(mape, 2) if mape is not None else None,
        bias=round(bias, 2),
        sample_count=n,
        model_version=model_version,
    )
