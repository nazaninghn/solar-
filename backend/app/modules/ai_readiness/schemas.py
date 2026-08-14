from datetime import datetime

from pydantic import BaseModel


class DataReadinessEntry(BaseModel):
    factory_id: int
    factory_name: str
    sample_count: int
    span_days: int
    complete_data_ratio: float
    ready_for_baseline_comparison: bool
    ready_for_seasonal_model: bool


class ReadinessSummary(BaseModel):
    total_factories_with_data: int
    ready_for_baseline_comparison: int
    ready_for_seasonal_model: int
    min_days_for_baseline_comparison: int
    min_days_for_seasonal_model: int


class ModelRegistryEntry(BaseModel):
    id: int
    type: str
    version: str
    status: str
    trained_at: datetime | None
    mae: float | None
    rmse: float | None
    mape: float | None
    description: str | None
    model_config = {"from_attributes": True}


class DriftEntry(BaseModel):
    forecast_type: str
    recent_mae: float | None
    recent_sample_count: int
    prior_mae: float | None
    prior_sample_count: int
    drift_percent: float | None
    drifted: bool


class AiReadinessDashboardResponse(BaseModel):
    data_readiness_summary: ReadinessSummary
    data_readiness_by_factory: list[DataReadinessEntry]
    model_registry: list[ModelRegistryEntry]
    drift: list[DriftEntry]
