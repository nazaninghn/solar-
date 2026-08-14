"""
STEP 33.17: Device Gateway API endpoints.

Telemetry, health, and capabilities for devices.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_ENERGY, VIEW_ENERGY
from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.device import Device
from app.models.factory import Factory
from app.models.user import User
from app.modules.gateway.health_monitor import run_health_check_all
from app.modules.gateway.models import DeviceCapability, DeviceTelemetry
from app.modules.gateway.schemas import (
    DeviceCapabilityResponse,
    DeviceHealthStatus,
    DeviceTelemetryResponse,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/gateway",
    tags=["Device Gateway"],
)


@router.get("/telemetry", response_model=list[DeviceTelemetryResponse])
def get_factory_telemetry(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    limit: int = 100,
):
    """Get recent telemetry for all devices in factory."""
    device_ids = [
        d.id for d in db.query(Device.id).filter(Device.factory_id == factory.id).all()
    ]
    if not device_ids:
        return []

    records = (
        db.query(DeviceTelemetry)
        .filter(DeviceTelemetry.device_id.in_(device_ids))
        .order_by(DeviceTelemetry.timestamp.desc())
        .limit(limit)
        .all()
    )
    return records


@router.get("/devices/{device_id}/telemetry", response_model=list[DeviceTelemetryResponse])
def get_device_telemetry(
    device_id: int,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    """Get telemetry for a specific device."""
    device = db.query(Device).filter(
        Device.id == device_id, Device.factory_id == factory.id
    ).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    records = (
        db.query(DeviceTelemetry)
        .filter(DeviceTelemetry.device_id == device_id)
        .order_by(DeviceTelemetry.timestamp.desc())
        .limit(limit)
        .all()
    )
    return records


@router.get("/devices/{device_id}/capabilities", response_model=list[DeviceCapabilityResponse])
def get_device_capabilities(
    device_id: int,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """Get capabilities for a device."""
    device = db.query(Device).filter(
        Device.id == device_id, Device.factory_id == factory.id
    ).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    return (
        db.query(DeviceCapability)
        .filter(DeviceCapability.device_id == device_id)
        .all()
    )


@router.get("/health", response_model=list[DeviceHealthStatus])
def check_all_devices_health(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """33.10: Run health check on all factory devices."""
    changes = run_health_check_all(db=db, factory_id=factory.id)

    # Return current status of all devices
    devices = db.query(Device).filter(
        Device.factory_id == factory.id,
        Device.is_active == True,
    ).all()

    results = []
    for d in devices:
        issues = []
        if d.status == "OFFLINE":
            issues.append("Device not responding")
        if d.status == "DEGRADED":
            issues.append("Data may be stale")
        if d.consecutive_error_count > 0:
            issues.append(f"{d.consecutive_error_count} consecutive errors")

        health_score = 100
        if d.status == "DEGRADED":
            health_score = 60
        elif d.status == "OFFLINE":
            health_score = 0
        elif d.consecutive_error_count > 0:
            health_score = max(50, 100 - d.consecutive_error_count * 10)

        results.append(DeviceHealthStatus(
            device_id=d.id,
            status=d.status,
            last_seen_at=d.last_seen_at,
            health_score=health_score,
            issues=issues,
        ))

    return results
