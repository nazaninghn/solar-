from enum import Enum


class BatteryAction(str, Enum):
    CHARGE = "charge"
    HOLD = "hold"
    DISCHARGE = "discharge"


def decide_battery_action(
    soc_percent: float,
    solar_surplus_kwh: float,
    grid_price_level: str,
    expected_solar_reduction_percent: float,
):
    if expected_solar_reduction_percent >= 30 and soc_percent < 85:
        return BatteryAction.CHARGE

    if grid_price_level == "high" and soc_percent > 30:
        return BatteryAction.DISCHARGE

    if grid_price_level == "low" and solar_surplus_kwh <= 0 and soc_percent < 80:
        return BatteryAction.CHARGE

    if solar_surplus_kwh > 0 and soc_percent < 90:
        return BatteryAction.CHARGE

    return BatteryAction.HOLD


def calculate_confidence(
    weather_confidence: float,
    historical_data_quality: float,
) -> float:
    return round(
        weather_confidence * 0.6 + historical_data_quality * 0.4,
        2,
    )


def explain_battery_action(
    action: BatteryAction,
    soc_percent: float,
    solar_surplus_kwh: float,
    grid_price_level: str,
    expected_solar_reduction_percent: float,
) -> str:
    """
    Mirrors decide_battery_action's branches so the reason text always
    matches the actual decision (9.20 asks for a human-readable "reason"
    alongside the action, which decide_battery_action itself doesn't produce).
    """
    if expected_solar_reduction_percent >= 30 and soc_percent < 85:
        return (
            f"Expected solar production is {expected_solar_reduction_percent:.0f}% "
            "lower tomorrow; charging now to build reserve."
        )

    if grid_price_level == "high" and soc_percent > 30:
        return "Grid price is high; discharging battery to reduce grid draw."

    if grid_price_level == "low" and solar_surplus_kwh <= 0 and soc_percent < 80:
        return "Grid price is low and there's no solar surplus; charging from the grid while it's cheap."

    if solar_surplus_kwh > 0 and soc_percent < 90:
        return "Solar surplus available; charging battery."

    return "No action needed; battery level and conditions are within normal range."
