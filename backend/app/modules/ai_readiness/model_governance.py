"""
STEP 81: Model lifecycle governance. ForecastModelRegistry (Step 35)
already has a real lifecycle vocabulary (TRAINING/VALIDATION/SHADOW/
PRODUCTION/RETIRED) but no code has ever written a row to it — this
seeds it with the two models that are ACTUALLY running today (the
solar/load baselines), scored against their REAL accuracy history
(app.modules.forecasting.accuracy), not invented numbers.
"""

import math
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.forecasting.models import (
    MODEL_PRODUCTION,
    ForecastAccuracy,
    ForecastModelRegistry,
)

# The only two "models" actually in production today — see
# app/modules/forecasting/models_ml/{solar,load}_baseline.py.
_BASELINE_MODELS = (
    {"type": "SOLAR_GENERATION", "version": "solar-baseline-v1"},
    {"type": "LOAD", "version": "load-baseline-v1"},
)


def seed_model_registry(db: Session) -> list[ForecastModelRegistry]:
    """Create-or-update a ForecastModelRegistry row per baseline model,
    scored against real ForecastAccuracy history. Safe to call
    repeatedly (upsert by version)."""
    from app.modules.forecasting.models import Forecast

    seeded = []
    now = datetime.now(timezone.utc)

    for model in _BASELINE_MODELS:
        records = db.scalars(
            select(ForecastAccuracy)
            .join(Forecast, ForecastAccuracy.forecast_id == Forecast.id)
            .where(Forecast.type == model["type"])
            .limit(2000)
        ).all()

        mae = rmse = mape = None
        if records:
            n = len(records)
            errors = [r.error for r in records]
            abs_errors = [r.absolute_error for r in records]
            actuals = [r.actual_value for r in records]

            mae = round(sum(abs_errors) / n, 3)
            rmse = round(math.sqrt(sum(e ** 2 for e in errors) / n), 3)

            non_zero = [(ae, a) for ae, a in zip(abs_errors, actuals) if a != 0]
            if non_zero:
                mape = round(sum(ae / abs(a) for ae, a in non_zero) / len(non_zero) * 100, 2)

        existing = db.scalar(
            select(ForecastModelRegistry).where(ForecastModelRegistry.version == model["version"])
        )

        if existing is None:
            existing = ForecastModelRegistry(
                type=model["type"],
                version=model["version"],
                status=MODEL_PRODUCTION,
                created_at=now,
                description=(
                    "Rule-based baseline (historical hourly average with a linear "
                    "weather/day-of-week adjustment) — not a trained ML model. See "
                    "docs/ai/ai-ml-readiness-assessment.md."
                ),
            )
            db.add(existing)

        existing.mae = mae
        existing.rmse = rmse
        existing.mape = mape
        existing.trained_at = None  # never "trained" — it's a formula, not a fitted model
        seeded.append(existing)

    db.commit()
    for entry in seeded:
        db.refresh(entry)

    return seeded


def list_model_registry(db: Session) -> list[ForecastModelRegistry]:
    return db.scalars(select(ForecastModelRegistry)).all()
