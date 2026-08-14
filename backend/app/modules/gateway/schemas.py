"""STEP 33: Pydantic schemas for Device Gateway."""

from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryPayload(BaseModel):
    """33.7: Incoming telemetry from device."""

    device_id: str
    timestamp: datetime
    schema_version: int = 1
    soc: float | None = None
    power_kw: float | None = None
    voltage: float | None = None
    current_a: float | None = None
    temperature_c: float | None = None
    energy_kwh: float | None = None
    frequency_hz: float | None = None
    status: str | None = None


class CommandPayload(BaseModel):
    """33.12: Command to send to device."""

    command_id: str
    action_id: int | None = None
    device_id: str
    schema_version: int = 1
    command_type: str
    payload: dict = Field(default_factory=dict)
    timestamp: datetime


class CommandAck(BaseModel):
    """33.12: ACK from device."""

    command_id: str
    status: str  # accepted, rejected, error
    timestamp: datetime
    error: str | None = None


class DeviceCapabilityResponse(BaseModel):
    id: int
    device_id: int
    capability: str
    min_value: float | None
    max_value: float | None
    unit: str | None
    enabled: bool

    model_config = {"from_attributes": True}


class DeviceTelemetryResponse(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    metric: str
    value: float
    unit: str | None
    quality: str

    model_config = {"from_attributes": True}


class DeviceEventResponse(BaseModel):
    id: int
    device_id: int
    event_type: str
    severity: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class DeviceHealthStatus(BaseModel):
    device_id: int
    status: str
    last_seen_at: datetime | None
    health_score: int = Field(ge=0, le=100)
    issues: list[str] = Field(default_factory=list)
