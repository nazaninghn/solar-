"""
STEP 36.13: Constraint Engine.

Defines operational limits that no recommendation may violate.
"""

from dataclasses import dataclass


@dataclass
class BatteryConstraints:
    min_soc: float = 15.0  # %
    max_soc: float = 90.0  # %
    max_charge_power_kw: float = 500.0
    max_discharge_power_kw: float = 500.0
    efficiency: float = 0.92  # Round-trip
    capacity_kwh: float = 2000.0


@dataclass
class GridConstraints:
    max_import_kw: float = 2000.0
    max_export_kw: float = 1000.0
    export_allowed: bool = True


@dataclass
class FactoryConstraints:
    min_load_kw: float = 50.0
    max_load_kw: float = 3000.0
    working_hours_start: int = 8
    working_hours_end: int = 18


@dataclass
class OptimizationConstraints:
    """All constraints bundled together."""

    battery: BatteryConstraints
    grid: GridConstraints
    factory: FactoryConstraints

    @classmethod
    def default(cls) -> "OptimizationConstraints":
        return cls(
            battery=BatteryConstraints(),
            grid=GridConstraints(),
            factory=FactoryConstraints(),
        )


def validate_battery_action(
    action_type: str,
    current_soc: float,
    target_soc: float | None,
    power_kw: float | None,
    constraints: BatteryConstraints,
) -> tuple[bool, str | None]:
    """36.34: Guardrail check for battery actions."""
    if action_type == "DISCHARGE_BATTERY":
        if current_soc <= constraints.min_soc:
            return False, f"SOC {current_soc}% at or below minimum {constraints.min_soc}%"
        if target_soc is not None and target_soc < constraints.min_soc:
            return False, f"Target SOC {target_soc}% below minimum {constraints.min_soc}%"
        if power_kw is not None and power_kw > constraints.max_discharge_power_kw:
            return False, f"Power {power_kw}kW exceeds max discharge {constraints.max_discharge_power_kw}kW"

    elif action_type == "CHARGE_BATTERY":
        if current_soc >= constraints.max_soc:
            return False, f"SOC {current_soc}% at or above maximum {constraints.max_soc}%"
        if target_soc is not None and target_soc > constraints.max_soc:
            return False, f"Target SOC {target_soc}% above maximum {constraints.max_soc}%"
        if power_kw is not None and power_kw > constraints.max_charge_power_kw:
            return False, f"Power {power_kw}kW exceeds max charge {constraints.max_charge_power_kw}kW"

    return True, None
