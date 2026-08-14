"""STEP 40: Alert & Notification schemas."""

from datetime import datetime

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    factory_id: int
    type: str
    severity: str
    title: str
    description: str | None
    status: str
    started_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentResponse(BaseModel):
    id: int
    factory_id: int
    title: str
    severity: str
    status: str
    started_at: datetime
    resolved_at: datetime | None
    root_cause: str | None
    financial_impact: float | None

    model_config = {"from_attributes": True}


class AlertRuleResponse(BaseModel):
    id: int
    name: str
    type: str
    severity: str
    enabled: bool
    cooldown_seconds: int

    model_config = {"from_attributes": True}


class AcknowledgeRequest(BaseModel):
    pass


class ResolveRequest(BaseModel):
    reason: str


class AlertCommentCreate(BaseModel):
    comment: str


class AlertCommentResponse(BaseModel):
    id: int
    alert_id: int
    user_id: int
    comment: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertSummaryResponse(BaseModel):
    total_open: int
    critical: int
    high: int
    medium: int
    unacknowledged: int
    active_incidents: int


class OnCallShiftCreate(BaseModel):
    user_id: int
    role: str = "PRIMARY"
    starts_at: datetime
    ends_at: datetime


class OnCallShiftResponse(BaseModel):
    id: int
    factory_id: int
    user_id: int
    role: str
    starts_at: datetime
    ends_at: datetime

    model_config = {"from_attributes": True}


class CurrentOnCallResponse(BaseModel):
    role: str
    user_id: int | None
    user_name: str | None
    user_email: str | None
