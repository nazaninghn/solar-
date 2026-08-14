"""STEP 43: Event & Notification schemas."""

from datetime import datetime

from pydantic import BaseModel


class EventResponse(BaseModel):
    id: int
    event_type: str
    severity: str
    source: str | None
    occurred_at: datetime
    model_config = {"from_attributes": True}


class SystemAlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str | None
    status: str
    occurred_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: int
    type: str
    channel: str
    title: str
    message: str | None
    status: str
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class NotificationPreferenceUpdate(BaseModel):
    event_type: str
    channel: str
    enabled: bool
    minimum_severity: str = "LOW"


class QuietHoursUpdate(BaseModel):
    enabled: bool
    start_time: str = "23:00"
    end_time: str = "07:00"
    timezone: str = "UTC"


class NotificationRuleCreate(BaseModel):
    name: str
    event_type: str
    condition_json: str | None = None
    severity: str = "MEDIUM"
    channels_json: str = '["IN_APP"]'
    cooldown_seconds: int = 3600


class NotificationRuleResponse(BaseModel):
    id: int
    name: str
    event_type: str
    severity: str
    enabled: bool
    cooldown_seconds: int
    model_config = {"from_attributes": True}


class AcknowledgeRequest(BaseModel):
    note: str | None = None


class ResolveRequest(BaseModel):
    note: str | None = None


class UnreadCountResponse(BaseModel):
    count: int
