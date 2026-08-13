from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceCreate(BaseModel):
    name: str
    device_type: str
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    connection_type: str


class DeviceUpdate(BaseModel):
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    connection_type: str | None = None
    is_active: bool | None = None


class DeviceResponse(BaseModel):
    id: int
    factory_id: int
    name: str
    device_type: str
    manufacturer: str | None
    model: str | None
    serial_number: str | None
    connection_type: str
    is_active: bool
    status: str
    last_seen_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceCreatedResponse(DeviceResponse):
    # 26.15-26.16: shown exactly once, at creation time — the hash is
    # all that's ever stored, so this is the device owner's only chance
    # to see the raw key. Same principle applies to regenerate-key.
    device_key: str


class DeviceStatusResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    last_seen_at: datetime | None


class TestConnectionResponse(BaseModel):
    success: bool
    latency_ms: float | None = None
    error: str | None = None


class DeviceKeyResponse(BaseModel):
    device_key: str


class TelemetryIngestRequest(BaseModel):
    # 26.8-26.9: standard fields are typed; anything else (e.g. a
    # manufacturer's own "mppt_1_voltage") is captured via extra="allow"
    # and stored verbatim in raw_data — the point of the pattern is that
    # a new manufacturer never requires a schema/migration change.
    model_config = ConfigDict(extra="allow")

    timestamp: datetime
    power_kw: float | None = None
    energy_kwh: float | None = None
    voltage: float | None = None
    current: float | None = None
    frequency: float | None = None
    soc_percent: float | None = None
    temperature_c: float | None = None
    status: str | None = None


class TelemetryIngestResponse(BaseModel):
    id: int
    recorded: bool
    duplicate: bool
