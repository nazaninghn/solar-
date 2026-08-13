from datetime import date

from pydantic import BaseModel


class WeatherForecast(BaseModel):
    condition: str
    cloud_coverage: float


class SolarForecast(BaseModel):
    baseline_kwh: float
    forecast_kwh: float
    reduction_percent: float


class FactoryForecastResponse(BaseModel):
    factory_id: int
    forecast_date: date
    weather: WeatherForecast
    solar: SolarForecast
