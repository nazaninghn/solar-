"""
STEP 35.11: Forecast Model Interface.

All forecast models implement this interface regardless of complexity.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ForecastResult:
    """Output of a forecast model for a single timestamp."""

    timestamp: datetime
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float


class BaseForecastModel(ABC):
    """35.11: Abstract interface for all forecast models."""

    @abstractmethod
    def predict(
        self,
        features: dict,
        timestamps: list[datetime],
    ) -> list[ForecastResult]:
        """Generate predictions for given timestamps."""
        ...

    @abstractmethod
    def version(self) -> str:
        """Return model version string."""
        ...

    @abstractmethod
    def model_type(self) -> str:
        """Return forecast type (SOLAR_GENERATION, LOAD, etc.)."""
        ...
