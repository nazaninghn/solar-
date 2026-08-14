"""
STEP 39.11-39.12: Heartbeat Monitor.

Processes heartbeat messages and updates device/gateway online status.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.device import Device
from app.modules.iot_gateway.models import Gateway
from app.modules.iot_gateway.schemas import HeartbeatMessage

logger = logging.getLogger(__name__)


def process_heartbeat(db: Session, heartbeat: HeartbeatMessage) -> dict:
    """Process incoming heartbeat and update device status."""
    now = datetime.now(timezone.utc)

    # Update device
    device = (
        db.query(Device)
        .filter(Device.id == int(heartbeat.device_id) if heartbeat.device_id.isdigit() else Device.name == heartbeat.device_id)
        .first()
    )
    if device:
        device.last_seen_at = now
        if device.status in ("OFFLINE", "UNKNOWN"):
            device.status = "ONLINE"
            logger.info(f"Device {device.id} recovered to ONLINE")
        device.consecutive_error_count = 0

    # Update gateway if present
    if heartbeat.gateway_id:
        gateway = db.query(Gateway).filter(Gateway.gateway_id == heartbeat.gateway_id).first()
        if gateway:
            gateway.last_seen_at = now
            gateway.status = "ONLINE"
            if heartbeat.uptime_seconds:
                gateway.uptime_seconds = heartbeat.uptime_seconds
            if heartbeat.signal_quality:
                gateway.signal_quality = heartbeat.signal_quality

    db.commit()
    return {"status": "OK", "device_id": heartbeat.device_id}


def check_offline_devices(db: Session, factory_id: int, threshold_seconds: int = 300) -> list[dict]:
    """
    39.12: Mark devices as OFFLINE/DEGRADED if heartbeat/telemetry is stale.
    """
    now = datetime.now(timezone.utc)
    offline_threshold = now - timedelta(seconds=threshold_seconds)
    degraded_threshold = now - timedelta(seconds=threshold_seconds // 2)

    devices = db.query(Device).filter(
        Device.factory_id == factory_id,
        Device.is_active == True,
        Device.status.in_(["ONLINE", "DEGRADED"]),
    ).all()

    changes = []
    for device in devices:
        if not device.last_seen_at:
            continue

        if device.last_seen_at < offline_threshold and device.status != "OFFLINE":
            old = device.status
            device.status = "OFFLINE"
            changes.append({"device_id": device.id, "old": old, "new": "OFFLINE"})
            logger.warning(f"Device {device.id} marked OFFLINE (last seen: {device.last_seen_at})")

        elif device.last_seen_at < degraded_threshold and device.status == "ONLINE":
            device.status = "DEGRADED"
            changes.append({"device_id": device.id, "old": "ONLINE", "new": "DEGRADED"})

    if changes:
        db.commit()
    return changes
