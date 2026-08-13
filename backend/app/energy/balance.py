from app.models.energy_reading import EnergyReading

# 26.22: "اگر اختلاف غیرمنطقی بود" — a relative tolerance, not an exact
# match. Real meters, clock skew between devices, and the hold-until-
# next-sample integration in aggregate_device_power_to_energy all
# introduce some slack; only a genuinely implausible mismatch (missing
# meter, wiring fault, wrong device mapping) should alert. The absolute
# floor keeps tiny-magnitude hours (a factory idle overnight) from
# flagging on noise.
RELATIVE_TOLERANCE = 0.15
MIN_ABSOLUTE_TOLERANCE_KWH = 5.0


def check_energy_balance(reading: EnergyReading) -> dict | None:
    """
    26.21-26.22: Solar + Grid Import + Battery Discharge should
    approximately equal Consumption + Grid Export + Battery Charge.
    Returns a violation dict (diff_kwh, supply_kwh, demand_kwh,
    tolerance_kwh) if the mismatch exceeds tolerance, else None.
    """
    supply_kwh = (
        reading.solar_generation_kwh
        + reading.grid_import_kwh
        + reading.battery_discharge_kwh
    )
    demand_kwh = (
        reading.consumption_kwh + reading.grid_export_kwh + reading.battery_charge_kwh
    )

    diff_kwh = supply_kwh - demand_kwh
    tolerance_kwh = max(
        MIN_ABSOLUTE_TOLERANCE_KWH, RELATIVE_TOLERANCE * max(supply_kwh, demand_kwh)
    )

    if abs(diff_kwh) <= tolerance_kwh:
        return None

    return {
        "diff_kwh": round(diff_kwh, 2),
        "supply_kwh": round(supply_kwh, 2),
        "demand_kwh": round(demand_kwh, 2),
        "tolerance_kwh": round(tolerance_kwh, 2),
    }
