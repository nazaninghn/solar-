"""
STEP 35.10: Load Baseline Forecast Model.

MVP: Historical average consumption by hour + day-of-week adjustment.
"""

from datetime import datetime, timezone

from app.modules.forecasting.models_ml.base import BaseForecastModel, ForecastResult


class LoadBaselineModel(BaseForecastModel):
    """
    35.10: Same-hour historical average for factory load.

    Logic:
    1. Use average consumption for same hour from recent history
    2. Adjust by day-of-week factor (weekday vs weekend)
    3. Apply working hours multiplier
    """

    def __init__(
        self,
        historical_hourly: dict[int, float] | None = None,
        working_hours: tuple[int, int] = (8, 18),
        weekend_factor: float = 0.3,
    ):
        self._historical = historical_hourly or self._default_load_curve()
        self._working_start, self._working_end = working_hours
        self._weekend_factor = weekend_factor

    def predict(
        self,
        features: dict,
        timestamps: list[datetime],
    ) -> list[ForecastResult]:
        results: list[ForecastResult] = []

        for ts in timestamps:
            hour = ts.hour
            base_kw = self._historical.get(hour, 200.0)

            # Day-of-week adjustment (35.6)
            is_weekend = ts.weekday() >= 5
            if is_weekend:
                base_kw *= self._weekend_factor

            predicted = base_kw

            # Confidence (load is more predictable than solar)
            hours_ahead = max(1, (ts - datetime.now(timezone.utc)).total_seconds() / 3600)
            horizon_penalty = min(0.15, hours_ahead * 0.003)
            confidence = max(0.5, 0.95 - horizon_penalty)

            # Prediction interval
            spread = predicted * (1 - confidence)
            lower = max(0, predicted - spread)
            upper = predicted + spread

            results.append(ForecastResult(
                timestamp=ts,
                predicted_value=round(predicted, 2),
                lower_bound=round(lower, 2),
                upper_bound=round(upper, 2),
                confidence=round(confidence, 3),
            ))

        return results

    def version(self) -> str:
        return "load-baseline-v1"

    def model_type(self) -> str:
        return "LOAD"

    def _default_load_curve(self) -> dict[int, float]:
        """Default factory load curve — high during working hours."""
        curve = {}
        for h in range(24):
            if 8 <= h <= 17:
                curve[h] = 450.0  # Working hours load
            elif 6 <= h <= 8 or 17 <= h <= 20:
                curve[h] = 280.0  # Ramp up/down
            else:
                curve[h] = 120.0  # Night baseline
        return curve
