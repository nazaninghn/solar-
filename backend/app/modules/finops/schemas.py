from datetime import date, datetime

from pydantic import BaseModel


class InfrastructureCostCreate(BaseModel):
    name: str
    category: str
    monthly_cost_usd: float
    notes: str | None = None
    effective_from: date | None = None


class InfrastructureCostResponse(BaseModel):
    id: int
    name: str
    category: str
    monthly_cost_usd: float
    effective_from: date
    effective_to: date | None
    notes: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class CostAttributionEntry(BaseModel):
    organization_id: int
    request_count: int
    usage_share_percent: float
    estimated_cost_usd: float


class CostAttributionResponse(BaseModel):
    total_monthly_cost_usd: float
    window_days: int
    organizations: list[CostAttributionEntry]


class BudgetThresholdCreate(BaseModel):
    name: str
    monthly_budget_usd: float
    warning_percent: float = 80.0


class BudgetThresholdResponse(BaseModel):
    id: int
    name: str
    monthly_budget_usd: float
    warning_percent: float
    created_at: datetime
    model_config = {"from_attributes": True}


class TableStorageEntry(BaseModel):
    table_name: str
    size_bytes: int
    size_mb: float


class StorageReportResponse(BaseModel):
    tables: list[TableStorageEntry]
    total_high_volume_bytes: int
    database_total_bytes: int
    capacity_gb: float
    percent_of_capacity: float
