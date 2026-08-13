def calculate_battery_savings(
    battery_energy_kwh: float,
    battery_efficiency: float,
    grid_price_per_kwh: float,
) -> float:
    usable_energy = battery_energy_kwh * battery_efficiency

    return round(usable_energy * grid_price_per_kwh, 2)


def calculate_sell_revenue(
    surplus_kwh: float,
    sell_price_per_kwh: float,
) -> float:
    return round(surplus_kwh * sell_price_per_kwh, 2)
