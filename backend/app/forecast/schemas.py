from datetime import datetime

from pydantic import BaseModel


class SolarForecastPoint(BaseModel):
    timestamp: datetime

    expected_power_kw: float
    expected_energy_kwh: float

    confidence: float


class SolarForecastResponse(BaseModel):
    factory_id: int
    is_stale: bool
    forecast: list[SolarForecastPoint]


class EnergyForecastPoint(BaseModel):
    timestamp: datetime

    expected_solar_kwh: float
    expected_consumption_kwh: float
    expected_balance_kwh: float


class EnergyForecastResponse(BaseModel):
    factory_id: int
    is_stale: bool
    forecast: list[EnergyForecastPoint]
