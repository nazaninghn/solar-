from enum import Enum


class EnergyAction(str, Enum):
    USE_SOLAR = "USE_SOLAR"
    CHARGE_BATTERY = "CHARGE_BATTERY"
    DISCHARGE_BATTERY = "DISCHARGE_BATTERY"
    BUY_FROM_GRID = "BUY_FROM_GRID"
    SELL_TO_GRID = "SELL_TO_GRID"
    SHIFT_LOAD = "SHIFT_LOAD"


def decide_energy_action(
    solar_power_kw,
    factory_load_kw,
    battery_soc,
    battery_min_soc,
    battery_max_soc,
    grid_buy_price,
    grid_sell_price,
):
    if solar_power_kw >= factory_load_kw:
        surplus = solar_power_kw - factory_load_kw

        if battery_soc < battery_max_soc:
            return {"action": EnergyAction.CHARGE_BATTERY, "amount_kw": surplus}

        if grid_sell_price > 0:
            return {"action": EnergyAction.SELL_TO_GRID, "amount_kw": surplus}

        # 18.21's original code falls through here with no return when
        # the battery is already full AND selling isn't attractive
        # (grid_sell_price <= 0) — solar is still covering the full
        # load either way, so that's the honest state to report rather
        # than implicitly returning None.
        return {"action": EnergyAction.USE_SOLAR, "amount_kw": factory_load_kw}

    deficit = factory_load_kw - solar_power_kw

    if battery_soc > battery_min_soc:
        return {"action": EnergyAction.DISCHARGE_BATTERY, "amount_kw": deficit}

    return {"action": EnergyAction.BUY_FROM_GRID, "amount_kw": deficit}
