"""STEP 34: Pipeline Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class MetricCatalogResponse(BaseModel):
    id: int
    key: str
    name: str
    unit: str
    min_value: float | None
    max_value: float | None
    aggregation: str
    enabled: bool

    model_config = {"from_attributes": True}


class DailyEnergySummaryResponse(BaseModel):
    id: int
    factory_id: int
    date: str
    solar_generation_kwh: float
    factory_consumption_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    estimated_cost: float
    estimated_savings: float
    peak_power_kw: float | None
    data_quality: str
    data_quality_score: int

    model_config = {"from_attributes": True}


class DataQualityResponse(BaseModel):
    factory_id: int
    date: str
    score: int = Field(ge=0, le=100)
    completeness: float
    freshness: float
    validity: float
    device_coverage: float

    model_config = {"from_attributes": True}


class EnergyKPIResponse(BaseModel):
    """34.23: Computed energy KPIs."""

    solar_coverage: float  # Solar Used / Consumption
    grid_dependency: float  # Grid Import / Consumption
    battery_utilization: float  # Battery cycles used
    peak_demand_kw: float
    total_savings: float
    export_revenue: float
    data_quality_score: int


class AggregationBucketResponse(BaseModel):
    metric: str
    bucket_start: datetime
    min_value: float
    max_value: float
    avg_value: float
    sum_value: float
    sample_count: int
    quality_summary: str

    model_config = {"from_attributes": True}
