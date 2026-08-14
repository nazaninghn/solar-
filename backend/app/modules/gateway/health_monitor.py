"""
STEP 33.10: Device Health Monitor.

Checks device freshness and marks devices as OFFLINE/DEGRADED
when telemetry or heartbeat stops arriving.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.device import Device

logger = logging.getLogger(__name__)

# Thresholds
OFFLINE_THRESHOLD = timedelta(minutes=10)
DEGRADED_THRESHOLD = timedelta(minutes=5)


def check_device_health(db: Session, device: Device) -> str:
    """
    33.10: Determine device health status based on last_seen_at.
    Returns new status: ONLINE, DEGRADED, or OFFLINE.
    """
    if not device.is_active:
        return "DISABLED"

    if device.last_seen_at is None:
        return "UNKNOWN"

    now = datetime.now(timezone.utc)
    age = now - device.last_seen_at

    if age > OFFLINE_THRESHOLD:
        return "OFFLINE"
    elif age > DEGRADED_THRESHOLD:
        return "DEGRADED"
    else:
        return "ONLINE"


def run_health_check_all(db: Session, factory_id: int) -> list[dict]:
    """
    Run health check for all devices in a factory.
    Updates status and returns list of status changes.
    """
    devices = db.query(Device).filter(
        Device.factory_id == factory_id,
        Device.is_active == True,
    ).all()

    changes: list[dict] = []

    for device in devices:
        new_status = check_device_health(db, device)
        old_status = device.status

        if new_status != old_status:
            device.status = new_status
            changes.append({
                "device_id": device.id,
                "name": device.name,
                "old_status": old_status,
                "new_status": new_status,
            })
            logger.info(
                f"Device {device.id} ({device.name}): {old_status} → {new_status}",
                extra={"device_id": device.id, "factory_id": factory_id},
            )

    if changes:
        db.commit()

    return changes
