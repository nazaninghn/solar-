"""STEP 35: Forecast Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ForecastPointResponse(BaseModel):
    timestamp: datetime
    predicted_value: float
    lower_bound: float | None
    upper_bound: float | None
    confidence: float

    model_config = {"from_attributes": True}


class ForecastResponse(BaseModel):
    id: int
    factory_id: int
    type: str
    model_version: str
    resolution: str
    confidence: float
    generated_at: datetime
    forecast_start: datetime
    forecast_end: datetime
    status: str
    points: list[ForecastPointResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ForecastAccuracyResponse(BaseModel):
    forecast_type: str
    horizon: str
    mae: float
    rmse: float
    mape: float | None
    bias: float
    sample_count: int


class ForecastSummaryResponse(BaseModel):
    """Quick summary for dashboard."""

    solar_forecast_kwh: float
    load_forecast_kwh: float
    net_energy_kwh: float
    confidence: float
    model_version: str
    generated_at: datetime | None
