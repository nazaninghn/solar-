"""
STEP 35.10: Solar Baseline Forecast Model.

MVP strategy: Weather-adjusted historical average.
Uses previous days' production scaled by cloud coverage forecast.
"""

import math
from datetime import datetime, timedelta, timezone

from app.modules.forecasting.models_ml.base import BaseForecastModel, ForecastResult


class SolarBaselineModel(BaseForecastModel):
    """
    35.10: Weather-adjusted baseline for solar generation.

    Logic:
    1. Use average production for same hour from historical data
    2. Adjust by cloud coverage forecast (0=clear → 1.0x, 100=overcast → 0.1x)
    3. Apply panel capacity scaling
    4. Generate confidence intervals based on historical variance
    """

    def __init__(
        self,
        historical_hourly: dict[int, float] | None = None,
        panel_capacity_kw: float = 500.0,
        cloud_forecast: dict[int, float] | None = None,
    ):
        """
        Args:
            historical_hourly: {hour: avg_kw} from past data
            panel_capacity_kw: Installed solar capacity
            cloud_forecast: {hour: cloud_pct 0-100} from weather
        """
        self._historical = historical_hourly or self._default_solar_curve()
        self._capacity = panel_capacity_kw
        self._cloud = cloud_forecast or {}

    def predict(
        self,
        features: dict,
        timestamps: list[datetime],
    ) -> list[ForecastResult]:
        results: list[ForecastResult] = []

        for ts in timestamps:
            hour = ts.hour
            base_kw = self._historical.get(hour, 0.0)

            # Weather adjustment (35.7)
            cloud_pct = self._cloud.get(hour, features.get("cloud_cover", 30))
            weather_factor = max(0.1, 1.0 - (cloud_pct / 120.0))

            predicted = base_kw * weather_factor

            # Confidence decreases with cloud uncertainty and forecast horizon
            hours_ahead = max(1, (ts - datetime.now(timezone.utc)).total_seconds() / 3600)
            horizon_penalty = min(0.2, hours_ahead * 0.005)
            cloud_penalty = cloud_pct * 0.002
            confidence = max(0.4, 0.92 - horizon_penalty - cloud_penalty)

            # Prediction interval (35.15)
            spread = predicted * (1 - confidence) * 1.5
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
        return "solar-baseline-v1"

    def model_type(self) -> str:
        return "SOLAR_GENERATION"

    def _default_solar_curve(self) -> dict[int, float]:
        """Default solar production curve (fraction of capacity by hour)."""
        # Approximate bell curve peaking at noon
        curve = {}
        for h in range(24):
            if 6 <= h <= 20:
                # Sine-based solar curve
                angle = math.pi * (h - 6) / 14
                curve[h] = self._capacity * math.sin(angle) * 0.7
            else:
                curve[h] = 0.0
        return curve
