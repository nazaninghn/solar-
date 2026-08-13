from datetime import date, datetime

from pydantic import BaseModel, Field


class EnergyReadingCreate(BaseModel):
    timestamp: datetime

    solar_generation_kwh: float = Field(default=0, ge=0)
    consumption_kwh: float = Field(default=0, ge=0)
    grid_import_kwh: float = Field(default=0, ge=0)
    grid_export_kwh: float = Field(default=0, ge=0)
    battery_charge_kwh: float = Field(default=0, ge=0)
    battery_discharge_kwh: float = Field(default=0, ge=0)

    battery_soc_percent: float | None = Field(default=None, ge=0, le=100)


class EnergyReadingResponse(EnergyReadingCreate):
    id: int
    factory_id: int

    model_config = {"from_attributes": True}


class CurrentEnergyResponse(BaseModel):
    solar_power_kw: float
    factory_load_kw: float
    battery_soc: float
    # 26.20's convention, applied consistently to both signals: positive
    # battery_power_kw = charging, negative = discharging; positive
    # grid_power_kw = net importing, negative = net exporting (grid_
    # import_kw/grid_export_kw below are always non-negative — use those
    # when you need the two directions split out rather than netted).
    battery_power_kw: float = 0.0
    grid_power_kw: float
    grid_import_kw: float = 0.0
    grid_export_kw: float = 0.0
    grid_status: str
    timestamp: datetime | None = None


class EnergyHistoryPoint(BaseModel):
    timestamp: datetime | date
    solar_kwh: float
    consumption_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    data_quality: str = "COMPLETE"


class EnergyHistoryResponse(BaseModel):
    resolution: str
    data: list[EnergyHistoryPoint]


class EnergySummaryResponse(BaseModel):
    solar_generation_kwh: float
    consumption_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    self_consumption_percent: float
    solar_coverage_percent: float
