"""STEP 41: Observability schemas."""

from datetime import datetime

from pydantic import BaseModel


class DataSourceResponse(BaseModel):
    id: int
    type: str
    name: str
    status: str
    last_success_at: datetime | None
    last_error_at: datetime | None
    consecutive_failures: int
    latency_ms: int | None
    quality_score: int

    model_config = {"from_attributes": True}


class DataQualityEventResponse(BaseModel):
    id: int
    factory_id: int
    source_type: str
    metric: str | None
    issue_type: str
    severity: str
    observed_value: float | None
    expected_value: float | None
    started_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class SystemHealthResponse(BaseModel):
    api: str
    database: str
    queue: str
    mqtt: str
    weather_feed: str
    price_feed: str
    forecast: str
    overall: str


class FactoryHealthResponse(BaseModel):
    factory_id: int
    telemetry_freshness: str
    device_availability_pct: float
    data_quality_score: int
    forecast_confidence: float
    active_issues: int
    energy_balance_ok: bool


class EnergyBalanceCheck(BaseModel):
    """41.12: Energy balance validation result."""
    factory_id: int
    timestamp: datetime
    solar_kwh: float
    grid_import_kwh: float
    battery_discharge_kwh: float
    consumption_kwh: float
    battery_charge_kwh: float
    grid_export_kwh: float
    balance_error_kwh: float
    tolerance_kwh: float
    is_valid: bool
