from datetime import datetime

from pydantic import BaseModel


class WeatherPoint(BaseModel):
    timestamp: datetime

    temperature_c: float
    cloud_cover_percent: float
    humidity_percent: float
    wind_speed_mps: float

    solar_irradiance_w_m2: float | None = None

    condition: str
