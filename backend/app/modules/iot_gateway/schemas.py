"""STEP 39: IoT Gateway schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class GatewayRegisterRequest(BaseModel):
    gateway_id: str
    factory_id: int
    name: str
    serial_number: str | None = None
    firmware_version: str | None = None


class GatewayResponse(BaseModel):
    id: int
    factory_id: int
    gateway_id: str
    name: str
    status: str
    firmware_version: str | None
    last_seen_at: datetime | None
    uptime_seconds: int | None
    connected_devices: int
    is_enabled: bool

    model_config = {"from_attributes": True}


class GatewayHealthResponse(BaseModel):
    gateway_id: str
    status: str
    uptime_seconds: int | None
    connected_devices: int
    last_seen_at: datetime | None
    mqtt_status: str = "UNKNOWN"
    signal_quality: float | None


class MQTTTelemetryMessage(BaseModel):
    """39.8: Standard telemetry message contract."""
    message_id: str
    device_id: str
    factory_id: str
    timestamp: datetime
    sequence: int
    metrics: dict[str, float]
    quality: str = "GOOD"
    firmware_version: str | None = None


class MQTTCommandMessage(BaseModel):
    """39.9: Standard command message contract."""
    command_id: str
    device_id: str
    type: str
    timestamp: datetime
    expires_at: datetime | None = None
    payload: dict = Field(default_factory=dict)
    trace_id: str | None = None


class MQTTAckMessage(BaseModel):
    """39.10: Standard ACK message contract."""
    command_id: str
    device_id: str
    status: str  # ACCEPTED, REJECTED, ERROR
    timestamp: datetime
    error_code: str | None = None
    trace_id: str | None = None


class HeartbeatMessage(BaseModel):
    """39.11: Device/Gateway heartbeat."""
    device_id: str
    gateway_id: str | None = None
    timestamp: datetime
    sequence: int | None = None
    firmware_version: str | None = None
    uptime_seconds: int | None = None
    signal_quality: float | None = None


class DLQEntryResponse(BaseModel):
    id: int
    device_id: int | None
    topic: str
    error_code: str
    error_message: str | None
    attempt_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
