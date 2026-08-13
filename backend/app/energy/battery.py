def calculate_battery_limits(
    capacity_kwh: float,
    soc: float,
    min_soc: float,
    max_soc: float,
    max_charge_kw: float,
    max_discharge_kw: float,
):
    current_energy = capacity_kwh * soc / 100
    min_energy = capacity_kwh * min_soc / 100
    max_energy = capacity_kwh * max_soc / 100

    available_for_discharge = max(current_energy - min_energy, 0)
    available_for_charge = max(max_energy - current_energy, 0)

    return {
        "available_for_discharge_kwh": available_for_discharge,
        "available_for_charge_kwh": available_for_charge,
        "max_discharge_kw": min(max_discharge_kw, available_for_discharge),
        "max_charge_kw": min(max_charge_kw, available_for_charge),
    }
