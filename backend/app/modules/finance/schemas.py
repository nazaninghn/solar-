"""STEP 37: Financial Engine schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class TariffResponse(BaseModel):
    id: int
    factory_id: int
    name: str
    type: str
    currency: str
    effective_from: datetime
    effective_to: datetime | None
    version: str
    enabled: bool

    model_config = {"from_attributes": True}


class TariffCreate(BaseModel):
    name: str
    type: str = "TIME_OF_USE"
    currency: str = "EUR"
    effective_from: datetime
    effective_to: datetime | None = None
    rules_json: str | None = None


class DailyFinancialResponse(BaseModel):
    factory_id: int
    date: str
    grid_import_cost: float
    export_revenue: float
    solar_value: float
    battery_cost: float
    total_energy_cost: float
    baseline_cost: float
    estimated_savings: float
    net_energy_benefit: float
    currency: str
    data_quality: str

    model_config = {"from_attributes": True}


class MonthlyFinancialResponse(BaseModel):
    factory_id: int
    month: str
    grid_cost: float
    export_revenue: float
    solar_value: float
    battery_cost: float
    total_cost: float
    savings: float
    net_benefit: float
    vs_previous_month: float | None
    currency: str

    model_config = {"from_attributes": True}


class FinancialSummaryResponse(BaseModel):
    """Dashboard KPIs (37.19)."""
    today_grid_cost: float
    today_savings: float
    monthly_savings: float
    export_revenue: float
    solar_value: float
    net_benefit: float
    cost_reduction_pct: float
    grid_dependency_pct: float
    currency: str


class SavingsAttributionResponse(BaseModel):
    """37.21: Breakdown of savings by source."""
    solar_self_consumption: float
    battery_arbitrage: float
    load_shifting: float
    peak_reduction: float
    export_revenue: float
    total: float
    currency: str


class ROIResponse(BaseModel):
    """37.40: Return on investment."""
    initial_investment: float
    annual_benefit: float
    payback_months: float | None
    roi_pct: float | None
    currency: str
