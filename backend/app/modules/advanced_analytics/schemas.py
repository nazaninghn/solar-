"""STEP 45: Analytics schemas."""

from datetime import datetime

from pydantic import BaseModel


class EnergyKPIResponse(BaseModel):
    solar_generation_kwh: float
    consumption_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    self_consumption_rate: float | None
    solar_coverage_rate: float | None
    grid_dependency_rate: float | None
    renewable_share: float | None
    peak_demand_kw: float | None
    load_factor: float | None
    model_config = {"from_attributes": True}


class ForecastAccuracyMetrics(BaseModel):
    forecast_type: str
    mae: float
    rmse: float
    mape: float | None
    bias: float
    sample_count: int
    model_version: str


class AnomalyResponse(BaseModel):
    id: int
    factory_id: int
    device_id: int | None
    type: str
    severity: str
    detected_at: datetime
    observed_value: float | None
    expected_value: float | None
    deviation: float | None
    status: str
    model_config = {"from_attributes": True}


class DevicePerformanceResponse(BaseModel):
    device_id: int
    availability: float
    efficiency: float | None
    error_count: int
    production_kwh: float | None
    performance_ratio: float | None
    model_config = {"from_attributes": True}


class SavingsAttributionResponse(BaseModel):
    solar_self_consumption: float
    battery_arbitrage: float
    load_shifting: float
    peak_reduction: float
    grid_export: float
    optimization_recommendations: float
    total: float
    currency: str


class AnalyticsOverviewResponse(BaseModel):
    factory_id: int
    period: str
    solar_kwh: float
    consumption_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    solar_coverage_pct: float
    grid_dependency_pct: float
    peak_demand_kw: float
    total_savings: float
    forecast_accuracy_pct: float
    anomaly_count: int
    data_freshness: str
