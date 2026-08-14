"""
STEP 38.10-38.11: Safety Guards and Pre-Execution Checks.

Validates authorization, device state, capability, limits, and freshness
before any command is allowed to proceed.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.device import Device
from app.modules.gateway.models import DeviceCapability
from app.modules.orchestrator.models import Command, ControlLock

logger = logging.getLogger(__name__)

SAFETY_POLICY_VERSION = "v2"

# Limits (should come from factory config in production)
MIN_SOC = 15.0
MAX_SOC = 90.0
MAX_CHARGE_KW = 500.0
MAX_DISCHARGE_KW = 500.0
MAX_TEMP_C = 45.0
STALE_APPROVAL_MINUTES = 180  # 3 hours


def run_pre_execution_guard(
    db: Session,
    command: Command,
    device: Device,
    current_soc: float | None = None,
    current_temp: float | None = None,
) -> tuple[bool, str | None]:
    """
    38.11: Full pre-execution guard chain.
    Returns (passed, failure_reason).
    """
    # 1. Device online?
    if device.status != "ONLINE" or not device.is_active:
        return False, f"DEVICE_OFFLINE: status={device.status}, active={device.is_active}"

    # 2. Device has capability?
    capability = (
        db.query(DeviceCapability)
        .filter(
            DeviceCapability.device_id == device.id,
            DeviceCapability.capability == command.type,
            DeviceCapability.enabled == True,
        )
        .first()
    )
    if not capability:
        return False, f"CAPABILITY_MISSING: device {device.id} does not support {command.type}"

    # 3. Value within capability limits
    import json
    payload = json.loads(command.payload_json) if command.payload_json else {}
    power_kw = payload.get("power_kw") or payload.get("limit_kw")

    if power_kw is not None and capability.max_value is not None:
        if power_kw > capability.max_value:
            return False, f"OVER_LIMIT: requested {power_kw}kW > max {capability.max_value}kW"

    # 4. SOC limits
    if current_soc is not None:
        if "DISCHARGE" in command.type and current_soc <= MIN_SOC:
            return False, f"SAFETY_BLOCKED: SOC {current_soc}% at/below min {MIN_SOC}%"
        if "CHARGE" in command.type and current_soc >= MAX_SOC:
            return False, f"SAFETY_BLOCKED: SOC {current_soc}% at/above max {MAX_SOC}%"

    # 5. Temperature
    if current_temp is not None and current_temp >= MAX_TEMP_C:
        return False, f"SAFETY_BLOCKED: temperature {current_temp}°C >= {MAX_TEMP_C}°C"

    # 6. Command not expired (38.13)
    now = datetime.now(timezone.utc)
    if command.expires_at and command.expires_at < now:
        return False, f"EXPIRED: command expired at {command.expires_at}"

    # 7. Control lock (38.26) — check no other active lock on this device
    active_lock = (
        db.query(ControlLock)
        .filter(
            ControlLock.device_id == device.id,
            ControlLock.is_active == True,
            ControlLock.command_id != command.id,
            ControlLock.expires_at > now,
        )
        .first()
    )
    if active_lock:
        return False, f"DEVICE_LOCKED: locked by command {active_lock.command_id} until {active_lock.expires_at}"

    return True, None


def check_stale_approval(command: Command) -> bool:
    """38.12: Check if approval is still fresh enough for execution."""
    if not command.updated_at:
        return True  # No approval timestamp
    now = datetime.now(timezone.utc)
    age = now - command.updated_at
    return age < timedelta(minutes=STALE_APPROVAL_MINUTES)
