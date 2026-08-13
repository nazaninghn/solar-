from datetime import datetime

from pydantic import BaseModel, Field


class ProductionLineCreate(BaseModel):
    name: str
    power_kw: float = Field(gt=0)
    flexible: bool = False
    minimum_run_time_hours: float | None = Field(default=None, gt=0)
    priority: str = "MEDIUM"


class ProductionLineResponse(BaseModel):
    id: int
    factory_id: int
    name: str
    power_kw: float
    flexible: bool
    minimum_run_time_hours: float | None
    priority: str
    created_at: datetime

    model_config = {"from_attributes": True}
