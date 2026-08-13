from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.battery.strategy import BatteryAction


class BatteryCreate(BaseModel):
    capacity_kwh: float = Field(gt=0)
    usable_capacity_kwh: float = Field(gt=0)

    soc_percent: float = Field(default=0, ge=0, le=100)
    health_percent: float = Field(default=100, ge=0, le=100)
    cycle_count: int = Field(default=0, ge=0)

    max_charge_power_kw: float | None = Field(default=None, gt=0)
    max_discharge_power_kw: float | None = Field(default=None, gt=0)


class BatteryResponse(BaseModel):
    id: int
    factory_id: int
    capacity_kwh: float
    usable_capacity_kwh: float
    soc_percent: float
    health_percent: float
    cycle_count: int
    max_charge_power_kw: float | None
    max_discharge_power_kw: float | None
    updated_at: datetime


class BatteryRecommendationResponse(BaseModel):
    action: BatteryAction
    target_soc_percent: float
    reason: str
    confidence: float
