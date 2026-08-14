"""STEP 36: Optimization schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class SmartRecommendationResponse(BaseModel):
    id: int
    factory_id: int
    type: str
    title: str
    description: str
    status: str
    priority: str
    confidence: float
    score: float
    expected_savings: float
    expected_revenue: float
    savings_lower: float | None
    savings_upper: float | None
    start_time: datetime | None
    end_time: datetime | None
    expires_at: datetime | None
    reasoning: str | None
    reason_codes_json: str | None
    risk_score: float
    model_version: str | None
    created_at: datetime
    approved_at: datetime | None
    actual_savings: float | None

    model_config = {"from_attributes": True}


class FlexibleLoadResponse(BaseModel):
    id: int
    factory_id: int
    name: str
    power_kw: float
    energy_kwh: float
    earliest_start: int
    latest_end: int
    duration_minutes: int
    priority: str
    enabled: bool

    model_config = {"from_attributes": True}


class FlexibleLoadCreate(BaseModel):
    name: str
    power_kw: float = Field(gt=0)
    energy_kwh: float = Field(gt=0)
    earliest_start: int = Field(ge=0, le=23)
    latest_end: int = Field(ge=0, le=23)
    duration_minutes: int = Field(gt=0)
    priority: str = "MEDIUM"


class RecommendationMetricsResponse(BaseModel):
    total_generated: int
    total_approved: int
    total_rejected: int
    total_expired: int
    execution_success_rate: float
    total_expected_savings: float
    total_actual_savings: float
