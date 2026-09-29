from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IndicatorResponse(BaseModel):
    code: str
    category: str
    label: str
    value: float | None
    unit: str
    threshold: float | None
    score: float
    message: str


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    device_type: str
    assessed_at: datetime
    risk_score: float
    risk_level: str
    method: str
    ml_status: str
    model_version: str | None
    failure_probability: float | None
    horizon_minutes: int | None
    fault_type: str | None
    fault_type_confidence: float | None
    irradiance_source: str | None
    imputed_inputs: list[str] | None
    indicators: list[IndicatorResponse]
    top_reason: str | None
    recommended_action: str | None
    days_to_threshold: float | None
    data_points: int


class DeviceRiskResponse(BaseModel):
    device_id: int
    device_name: str
    device_type: str
    status: str
    assessment: AssessmentResponse | None


class RiskOverviewResponse(BaseModel):
    factory_id: int
    assessed_at: datetime | None
    counts: dict[str, int]
    devices: list[DeviceRiskResponse]


class RiskHistoryPoint(BaseModel):
    assessed_at: datetime
    risk_score: float
    risk_level: str
    failure_probability: float | None


class FailureEventCreate(BaseModel):
    device_id: int
    occurred_at: datetime
    resolved_at: datetime | None = None
    failure_type: str = Field(min_length=1, max_length=50)
    severity: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    description: str | None = None


class FailureEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    occurred_at: datetime
    resolved_at: datetime | None
    failure_type: str
    severity: str
    description: str | None
    reported_by_user_id: int | None
    created_at: datetime


class ModelInfoResponse(BaseModel):
    version: str
    source: str
    label: str
    horizon_minutes: int
    threshold: float
    daylight_irradiance_w_m2: float
    test_metrics: dict[str, float]
    lead_time: dict
    fault_type_version: str
    fault_types: list[str]
    fault_type_macro_f1: float
    limitations: list[str]
