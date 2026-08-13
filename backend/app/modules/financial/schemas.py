from datetime import date, datetime

from pydantic import BaseModel


class FinancialRecordResponse(BaseModel):
    id: int
    factory_id: int
    date: date

    solar_savings: float
    grid_purchase_cost: float
    battery_savings: float
    energy_sales_revenue: float

    total_savings: float
    net_energy_cost: float

    created_at: datetime

    model_config = {"from_attributes": True}


class FinancialSummaryResponse(BaseModel):
    total_savings: float
    solar_savings: float
    battery_savings: float
    energy_sales_revenue: float
    load_shift_savings: float
    total_revenue: float
    grid_purchase_cost: float
    net_energy_cost: float

    previous_period_savings: float
    savings_change_percent: float

    # Not in the brief's 12.14 schema, but the DoD checklist (12.29)
    # explicitly requires "Cost Reduction %", and 12.21-12.22 define how
    # to compute it — added as a field here rather than a separate endpoint.
    cost_reduction_percent: float


class MonthlyFinancialSummary(BaseModel):
    month: str
    grid_purchase_cost: float
    total_savings: float
    energy_sales_revenue: float


class FinancialKPIResponse(BaseModel):
    solar_contribution_percent: float
    grid_dependency_percent: float
    renewable_coverage_percent: float
    estimated_annual_benefit: float
    estimated_roi_percent: float | None
    estimated_payback_years: float | None


class FinancialTransactionResponse(BaseModel):
    id: int
    factory_id: int
    type: str
    energy_kwh: float
    unit_price: float
    amount: float
    timestamp: datetime
    description: str | None

    model_config = {"from_attributes": True}
