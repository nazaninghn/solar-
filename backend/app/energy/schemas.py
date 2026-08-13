from pydantic import BaseModel


class EnergyInput(BaseModel):
    solar_power_kw: float
    factory_load_kw: float

    battery_soc: float
    battery_available_kw: float
    battery_capacity_kwh: float

    grid_price_buy: float
    grid_price_sell: float


class EnergyBalance(BaseModel):
    solar_to_load_kw: float
    solar_to_battery_kw: float
    solar_to_grid_kw: float
    battery_to_load_kw: float
    grid_to_load_kw: float

    surplus_kw: float
    deficit_kw: float

    grid_import_required: bool
    grid_export_available: bool
