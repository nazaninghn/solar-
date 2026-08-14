from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class RecommendationType(str, Enum):
    CHARGE_BATTERY = "CHARGE_BATTERY"
    DISCHARGE_BATTERY = "DISCHARGE_BATTERY"
    BUY_FROM_GRID = "BUY_FROM_GRID"
    SELL_TO_GRID = "SELL_TO_GRID"
    SHIFT_LOAD = "SHIFT_LOAD"


class RecommendationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"


class RecommendationResponse(BaseModel):
    id: int
    factory_id: int
    type: str
    title: str
    description: str
    action: str
    start_time: datetime | None
    end_time: datetime | None
    estimated_savings: float
    estimated_revenue: float
    net_benefit: float | None
    confidence: float
    score: float | None
    status: RecommendationStatus
    created_at: datetime
    expires_at: datetime | None

    model_config = {"from_attributes": True}


class RejectRequest(BaseModel):
    reason: str | None = None


class ScenarioResponse(BaseModel):
    name: str
    applicable: bool
    total_cost: float
    grid_import_kwh: float
    grid_export_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    load_shifted_kwh: float
    explanation: str
    is_optimal: bool


class ScenarioComparisonResponse(BaseModel):
    imbalance_kwh: float
    scenarios: list[ScenarioResponse]
