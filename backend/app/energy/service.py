from app.energy.battery import calculate_battery_limits
from app.energy.calculator import calculate_energy_balance
from app.energy.cost import calculate_energy_cost
from app.energy.decision import decide_energy_action
from app.energy.schemas import EnergyInput


def calculate_energy_state(
    data: EnergyInput,
    battery_min_soc: float,
    battery_max_soc: float,
    battery_max_charge_kw: float,
    battery_max_discharge_kw: float,
) -> dict:
    """
    18.25's flow (Input -> Battery Limits -> Energy Balance -> Cost ->
    Decision). Takes the battery's min/max SOC and charge/discharge caps
    as separate parameters rather than folding them into EnergyInput,
    since 18.6's schema doesn't carry them but calculate_battery_limits
    (18.14) needs them before the balance step can run.
    """
    battery_limits = calculate_battery_limits(
        capacity_kwh=data.battery_capacity_kwh,
        soc=data.battery_soc,
        min_soc=battery_min_soc,
        max_soc=battery_max_soc,
        max_charge_kw=battery_max_charge_kw,
        max_discharge_kw=battery_max_discharge_kw,
    )

    # calculate_energy_balance takes one battery_available_kw, not
    # separate charge/discharge limits — but solar_to_load already
    # absorbs min(solar, load), so a single call only ever has a surplus
    # OR a deficit, never both. Pick whichever limit actually applies.
    if data.solar_power_kw >= data.factory_load_kw:
        battery_available_kw = battery_limits["max_charge_kw"]
    else:
        battery_available_kw = battery_limits["max_discharge_kw"]

    balance = calculate_energy_balance(
        solar_power_kw=data.solar_power_kw,
        factory_load_kw=data.factory_load_kw,
        battery_available_kw=battery_available_kw,
    )

    # Treats the instantaneous kW balance as kWh for a nominal one-hour
    # snapshot — this is a "current state" endpoint, not a metered
    # billing period, and Step 18 never defines a duration/interval
    # concept despite 18.9's own point about power vs. energy.
    cost = calculate_energy_cost(
        grid_import_kwh=balance["grid_to_load_kw"],
        grid_export_kwh=balance["solar_to_grid_kw"],
        buy_price=data.grid_price_buy,
        sell_price=data.grid_price_sell,
    )

    decision = decide_energy_action(
        solar_power_kw=data.solar_power_kw,
        factory_load_kw=data.factory_load_kw,
        battery_soc=data.battery_soc,
        battery_min_soc=battery_min_soc,
        battery_max_soc=battery_max_soc,
        grid_buy_price=data.grid_price_buy,
        grid_sell_price=data.grid_price_sell,
    )

    return {
        "battery": battery_limits,
        "balance": balance,
        "cost": cost,
        "decision": decision,
    }
