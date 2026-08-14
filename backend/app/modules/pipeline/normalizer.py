"""
STEP 34.7: Unit Normalization.

Converts device-specific units to standard SolarFlow units.
All power stored in kW, energy in kWh, temperature in °C.
"""

UNIT_CONVERSIONS: dict[str, tuple[str, float]] = {
    # (target_unit, multiplier)
    "W": ("kW", 0.001),
    "mW": ("kW", 0.000001),
    "MW": ("kW", 1000.0),
    "Wh": ("kWh", 0.001),
    "MWh": ("kWh", 1000.0),
    "mA": ("A", 0.001),
    "mV": ("V", 0.001),
}

# Standard metric key mapping (device field → standard key)
METRIC_KEY_MAP: dict[str, str] = {
    "state_of_charge": "soc",
    "battery_soc": "soc",
    "SoC": "soc",
    "active_power": "battery_power",
    "discharge_power": "battery_power",
    "charge_power": "battery_power",
    "pv_power": "solar_power",
    "solar_output": "solar_power",
    "grid_power": "grid_import_power",
    "consumption_power": "load_power",
    "load": "load_power",
    "temp": "temperature",
    "battery_temp": "temperature",
    "cell_temperature": "temperature",
}


def normalize_unit(value: float, source_unit: str) -> tuple[float, str]:
    """Convert a value from source_unit to standard unit."""
    if source_unit in UNIT_CONVERSIONS:
        target_unit, multiplier = UNIT_CONVERSIONS[source_unit]
        return value * multiplier, target_unit
    return value, source_unit


def normalize_metric_key(raw_key: str) -> str:
    """Map device-specific metric names to standard keys."""
    return METRIC_KEY_MAP.get(raw_key, raw_key)
