"""
STEP 32.9-32.12: Safety Engine.

Validates that an action is safe to execute before approval or execution.
Checks: device online, battery SOC limits, power limits, temperature.
"""

from sqlalchemy.orm import Session

from app.models.device import Device
from app.modules.control.models import EnergyAction, ACTION_CHARGE_BATTERY, ACTION_DISCHARGE_BATTERY
from app.modules.control.schemas import SafetyCheckResult

# Safety thresholds (could be per-factory config later)
MIN_SOC = 15.0
MAX_SOC = 90.0
MAX_CHARGE_POWER_KW = 500.0
MAX_DISCHARGE_POWER_KW = 500.0
MAX_BATTERY_TEMP_C = 45.0
DATA_FRESHNESS_SECONDS = 300  # 5 minutes


def run_safety_checks(
    db: Session,
    action: EnergyAction,
    device: Device,
    current_soc: float | None = None,
    current_temp: float | None = None,
) -> SafetyCheckResult:
    """32.9: Run all safety checks for an action. Returns pass/fail with details."""
    checks: list[dict] = []
    all_passed = True

    # 1. Device online check (32.12)
    device_online = device.status == "ONLINE" and device.is_active
    checks.append({
        "name": "device_online",
        "passed": device_online,
        "detail": f"Device status={device.status}, active={device.is_active}",
    })
    if not device_online:
        all_passed = False

    # 2. SOC limits (32.10)
    if current_soc is not None:
        if action.type == ACTION_DISCHARGE_BATTERY:
            soc_ok = current_soc > MIN_SOC
            target_ok = (action.target_soc or 0) >= MIN_SOC
            checks.append({
                "name": "soc_discharge_limit",
                "passed": soc_ok and target_ok,
                "detail": f"Current SOC={current_soc}%, min={MIN_SOC}%, target={action.target_soc}%",
            })
            if not (soc_ok and target_ok):
                all_passed = False

        elif action.type == ACTION_CHARGE_BATTERY:
            soc_ok = current_soc < MAX_SOC
            target_ok = (action.target_soc or 100) <= MAX_SOC
            checks.append({
                "name": "soc_charge_limit",
                "passed": soc_ok and target_ok,
                "detail": f"Current SOC={current_soc}%, max={MAX_SOC}%, target={action.target_soc}%",
            })
            if not (soc_ok and target_ok):
                all_passed = False

    # 3. Power limits (32.11)
    if action.target_power_kw is not None:
        max_power = MAX_CHARGE_POWER_KW if action.type == ACTION_CHARGE_BATTERY else MAX_DISCHARGE_POWER_KW
        power_ok = action.target_power_kw <= max_power
        checks.append({
            "name": "power_limit",
            "passed": power_ok,
            "detail": f"Requested={action.target_power_kw}kW, max={max_power}kW",
        })
        if not power_ok:
            all_passed = False

    # 4. Temperature safety (32.11)
    if current_temp is not None:
        temp_ok = current_temp < MAX_BATTERY_TEMP_C
        checks.append({
            "name": "temperature_safety",
            "passed": temp_ok,
            "detail": f"Current temp={current_temp}°C, max={MAX_BATTERY_TEMP_C}°C",
        })
        if not temp_ok:
            all_passed = False

    blocked_reason = None
    if not all_passed:
        failed = [c for c in checks if not c["passed"]]
        blocked_reason = "; ".join(c["detail"] for c in failed)

    return SafetyCheckResult(
        passed=all_passed,
        checks=checks,
        blocked_reason=blocked_reason,
    )
