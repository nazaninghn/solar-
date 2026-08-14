"""STEP 38: Control Orchestrator schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class CommandCreateRequest(BaseModel):
    device_id: int
    type: str
    payload: dict = Field(default_factory=dict)
    recommendation_id: int | None = None
    priority: str = "MEDIUM"
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None


class CommandResponse(BaseModel):
    id: int
    factory_id: int
    device_id: int
    recommendation_id: int | None
    type: str
    status: str
    priority: str
    failure_reason: str | None
    scheduled_at: datetime | None
    expires_at: datetime | None
    sent_at: datetime | None
    acked_at: datetime | None
    verified_at: datetime | None
    completed_at: datetime | None
    created_by: int | None
    approved_by: int | None
    attempt_count: int
    trace_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CommandVerificationResponse(BaseModel):
    id: int
    command_id: int
    metric: str
    expected_value: float
    actual_value: float | None
    tolerance: float
    status: str
    verified_at: datetime | None

    model_config = {"from_attributes": True}


class ControlStatusResponse(BaseModel):
    factory_id: int
    active_commands: int
    queued_commands: int
    executing_commands: int
    failed_today: int
    verified_today: int
    emergency_stop_active: bool


class EmergencyStopRequest(BaseModel):
    reason: str
