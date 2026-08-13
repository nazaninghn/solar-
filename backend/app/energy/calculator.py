def calculate_energy_balance(
    solar_power_kw: float,
    factory_load_kw: float,
    battery_available_kw: float,
):
    solar_to_load = min(solar_power_kw, factory_load_kw)

    remaining_solar = solar_power_kw - solar_to_load
    remaining_load = factory_load_kw - solar_to_load

    battery_to_load = 0
    solar_to_battery = 0
    grid_to_load = 0
    solar_to_grid = 0

    if remaining_solar > 0:
        solar_to_battery = min(remaining_solar, battery_available_kw)
        remaining_solar -= solar_to_battery

        if remaining_solar > 0:
            solar_to_grid = remaining_solar

    if remaining_load > 0:
        battery_to_load = min(remaining_load, battery_available_kw)
        remaining_load -= battery_to_load

        if remaining_load > 0:
            grid_to_load = remaining_load

    return {
        "solar_to_load_kw": solar_to_load,
        "solar_to_battery_kw": solar_to_battery,
        "solar_to_grid_kw": solar_to_grid,
        "battery_to_load_kw": battery_to_load,
        "grid_to_load_kw": grid_to_load,
        "surplus_kw": solar_to_grid,
        "deficit_kw": grid_to_load,
        "grid_import_required": grid_to_load > 0,
        "grid_export_available": solar_to_grid > 0,
    }
