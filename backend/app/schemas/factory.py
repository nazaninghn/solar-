from datetime import datetime, time

from pydantic import BaseModel, ConfigDict


class FactoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    address: str | None
    industry: str | None
    currency: str
    solar_capacity_kw: float | None
    battery_capacity_kwh: float | None
    solar_installation_cost: float | None
    created_at: datetime
    updated_at: datetime


class FactoryCreate(BaseModel):
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    industry: str | None = None
    currency: str | None = None
    solar_capacity_kw: float | None = None
    battery_capacity_kwh: float | None = None
    solar_installation_cost: float | None = None
    grid_connection_type: str | None = None
    electricity_tariff: str | None = None
    working_hours_start: time | None = None
    working_hours_end: time | None = None
    timezone: str | None = None


class FactoryUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    industry: str | None = None
    currency: str | None = None
    solar_capacity_kw: float | None = None
    battery_capacity_kwh: float | None = None
    solar_installation_cost: float | None = None
    grid_connection_type: str | None = None
    electricity_tariff: str | None = None
    working_hours_start: time | None = None
    working_hours_end: time | None = None
    timezone: str | None = None
