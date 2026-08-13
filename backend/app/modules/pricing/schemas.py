from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PriceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ElectricityPriceCreate(BaseModel):
    timestamp: datetime

    buy_price_per_kwh: float = Field(ge=0)
    sell_price_per_kwh: float = Field(ge=0)

    price_level: PriceLevel


class ElectricityPriceResponse(BaseModel):
    id: int
    factory_id: int
    timestamp: datetime
    buy_price_per_kwh: float
    sell_price_per_kwh: float
    price_level: str

    model_config = {"from_attributes": True}


class PriceAnalysisResponse(BaseModel):
    current: ElectricityPriceResponse | None
    cheapest: ElectricityPriceResponse | None
    most_expensive: ElectricityPriceResponse | None
    # 28.25: only meaningful for "current" — cheapest/most_expensive are
    # historical lookups, not something that goes stale.
    current_age_minutes: float | None = None
    current_is_stale: bool | None = None
