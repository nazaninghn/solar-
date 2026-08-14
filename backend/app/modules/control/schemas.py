"""STEP 32: Pydantic schemas for Energy Control."""

from datetime import datetime

from pydantic import BaseModel, Field


class ActionCreateRequest(BaseModel):
    """Request to create an energy action from a recommendation or manually."""

    recommendation_id: int | None = None
    device_id: int
    type: str = Field(..., description="CHARGE_BATTERY or DISCHARGE_BATTERY")
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    target_power_kw: float | None = None
    target_energy_kwh: float | None = None
    target_soc: float | None = None


class ActionResponse(BaseModel):
    id: int
    factory_id: int
    recommendation_id: int | None
    device_id: int | None
    type: str
    status: str
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    target_power_kw: float | None
    target_energy_kwh: float | None
    target_soc: float | None
    created_by: int | None
    approved_by: int | None
    created_at: datetime
    approved_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None

    model_config = {"from_attributes": True}


class ActionSummaryResponse(BaseModel):
    active: int
    scheduled: int
    completed_today: int
    failed_today: int


class CommandResponse(BaseModel):
    id: int
    action_id: int
    device_id: int
    command_type: str
    status: str
    attempt_count: int
    idempotency_key: str
    created_at: datetime
    sent_at: datetime | None
    completed_at: datetime | None
    error: str | None

    model_config = {"from_attributes": True}


class SafetyCheckResult(BaseModel):
    passed: bool
    checks: list[dict]
    blocked_reason: str | None = None
