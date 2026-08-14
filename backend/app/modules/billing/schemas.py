"""STEP 44: Billing & Settlement schemas."""

from datetime import datetime
from pydantic import BaseModel


class PlanResponse(BaseModel):
    id: int
    name: str
    currency: str
    monthly_price: float
    annual_price: float | None
    max_factories: int
    max_devices: int
    max_users: int
    active: bool
    model_config = {"from_attributes": True}


class SubscriptionResponse(BaseModel):
    id: int
    organization_id: int
    plan_id: int
    status: str
    billing_cycle: str
    current_period_start: datetime
    current_period_end: datetime
    trial_end: datetime | None
    model_config = {"from_attributes": True}


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    status: str
    currency: str
    subtotal: float
    discount: float
    tax: float
    total: float
    due_at: datetime | None
    paid_at: datetime | None
    period_start: datetime
    period_end: datetime
    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    id: int
    provider: str
    amount: float
    currency: str
    status: str
    paid_at: datetime | None
    model_config = {"from_attributes": True}


class SettlementResponse(BaseModel):
    id: int
    factory_id: int
    period_start: datetime
    period_end: datetime
    status: str
    currency: str
    import_cost: float
    export_revenue: float
    solar_value: float
    battery_value: float
    net_energy_cost: float
    finalized_at: datetime | None
    model_config = {"from_attributes": True}


class UsageResponse(BaseModel):
    metric: str
    quantity: float
    period_start: datetime
    period_end: datetime
    model_config = {"from_attributes": True}
