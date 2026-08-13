from pydantic import BaseModel


class EnergyRealtimeMessage(BaseModel):
    factory_id: int

    solar_power_kw: float
    factory_load_kw: float

    battery_soc: float
    battery_power_kw: float

    grid_power_kw: float
    grid_import_kw: float
    grid_export_kw: float

    grid_status: str

    timestamp: str
