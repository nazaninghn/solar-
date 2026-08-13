from datetime import date as date_type, datetime

from pydantic import BaseModel


class HourlyEnergyResponse(BaseModel):
    factory_id: int
    timestamp: datetime
    solar_generation_kwh: float
    factory_consumption_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    data_completeness: float
    data_quality: str


class DailyEnergyResponse(BaseModel):
    factory_id: int
    date: date_type
    solar_generation_kwh: float
    factory_consumption_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    battery_charge_kwh: float
    battery_discharge_kwh: float
    solar_coverage_percent: float
    grid_dependency_percent: float
    peak_demand_kw: float | None
    peak_demand_time: datetime | None
    peak_solar_kw: float | None
    data_completeness: float
    data_quality: str


class MonthlyEnergyResponse(BaseModel):
    factory_id: int
    month: str
    solar_generation_kwh: float
    factory_consumption_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float
    total_savings: float
    total_revenue: float
    data_completeness: float


class BackfillRequest(BaseModel):
    start: datetime
    end: datetime


class BackfillResponse(BaseModel):
    hours_processed: int
    days_processed: int
