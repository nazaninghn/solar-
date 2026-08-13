import secrets
import time
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.analytics.calculator import validate_power_reading, validate_soc_reading
from app.core.security import hash_token
from app.devices.factory import create_device_adapter
from app.devices.gateway import DeviceGateway
from app.devices.validation import MAX_PLAUSIBLE_POWER_KW, is_timestamp_plausible
from app.models.device import Device
from app.models.device_energy_reading import DeviceEnergyReading
from app.models.factory import Factory
from app.models.user import User

gateway = DeviceGateway()


def create_device(db: Session, factory_id: int, data) -> tuple[Device, str]:
    raw_key = secrets.token_urlsafe(32)

    device = Device(
        factory_id=factory_id,
        name=data.name,
        device_type=data.device_type,
        manufacturer=data.manufacturer,
        model=data.model,
        serial_number=data.serial_number,
        connection_type=data.connection_type,
        device_key_hash=hash_token(raw_key),
        created_at=datetime.now(timezone.utc),
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device, raw_key


def regenerate_device_key(db: Session, current_user: User, device_id: int) -> str:
    device = get_owned_device(db, current_user, device_id)

    raw_key = secrets.token_urlsafe(32)
    device.device_key_hash = hash_token(raw_key)
    db.commit()

    return raw_key


def get_devices(db: Session, factory_id: int) -> list[Device]:
    return db.scalars(
        select(Device).where(Device.factory_id == factory_id)
    ).all()


def get_device_status(db: Session, factory_id: int) -> list[dict]:
    devices = get_devices(db, factory_id)

    return [
        {
            "id": device.id,
            "name": device.name,
            "type": device.device_type,
            "status": device.status,
            "last_seen_at": device.last_seen_at,
        }
        for device in devices
    ]


def get_owned_device(db: Session, current_user: User, device_id: int) -> Device:
    """
    16.11's item-level endpoints (GET/PATCH/DELETE /api/v1/devices/{id})
    have no factory_id in their path — same shape as Step 14's
    PATCH /notifications/{id}/read. Ownership is validated the same way:
    joining through the device's own factory to the user's organization.
    """
    device = db.scalar(
        select(Device)
        .join(Factory, Factory.id == Device.factory_id)
        .where(
            Device.id == device_id,
            Factory.organization_id == current_user.organization_id,
        )
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return device


def update_device(db: Session, current_user: User, device_id: int, data) -> Device:
    device = get_owned_device(db, current_user, device_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)

    return device


def delete_device(db: Session, current_user: User, device_id: int) -> None:
    device = get_owned_device(db, current_user, device_id)

    db.delete(device)
    db.commit()


def ingest_telemetry(db: Session, device: Device, data) -> tuple[DeviceEnergyReading, bool]:
    """
    Returns (reading, was_duplicate). "was_duplicate" lets the endpoint
    distinguish "recorded" from "already had this one" without treating
    the latter as an error — 26.36's replay protection should be quiet,
    not a 4xx, since a device retrying a delivery it's unsure landed is
    normal, expected behavior.
    """
    if not is_timestamp_plausible(data.timestamp):
        raise ValueError(
            "Timestamp is outside the plausible window (too far in the past or future)"
        )

    if data.power_kw is not None:
        if abs(data.power_kw) > MAX_PLAUSIBLE_POWER_KW:
            raise ValueError("power_kw exceeds plausible bounds")
        if device.device_type in ("INVERTER", "GRID_METER", "FACTORY_METER") and not validate_power_reading(
            data.power_kw
        ):
            raise ValueError(f"power_kw cannot be negative for device_type {device.device_type}")

    if data.soc_percent is not None and not validate_soc_reading(data.soc_percent):
        raise ValueError("soc_percent must be between 0 and 100")

    raw_data = data.model_extra or None

    stmt = (
        insert(DeviceEnergyReading)
        .values(
            factory_id=device.factory_id,
            device_id=device.id,
            timestamp=data.timestamp,
            power_kw=data.power_kw if data.power_kw is not None else 0.0,
            energy_kwh=data.energy_kwh,
            voltage=data.voltage,
            current=data.current,
            frequency=data.frequency,
            soc_percent=data.soc_percent,
            temperature_c=data.temperature_c,
            raw_data=raw_data,
            status=data.status or "ONLINE",
        )
        .on_conflict_do_nothing(
            index_elements=["device_id", "timestamp"],
        )
        .returning(DeviceEnergyReading.id)
    )

    inserted_id = db.execute(stmt).scalar()
    was_duplicate = inserted_id is None

    device.last_seen_at = datetime.now(timezone.utc)
    device.status = data.status or "ONLINE"

    db.commit()

    if was_duplicate:
        reading = db.scalar(
            select(DeviceEnergyReading).where(
                DeviceEnergyReading.device_id == device.id,
                DeviceEnergyReading.timestamp == data.timestamp,
            )
        )
    else:
        reading = db.get(DeviceEnergyReading, inserted_id)

    return reading, was_duplicate


async def test_connection(db: Session, current_user: User, device_id: int) -> dict:
    device = get_owned_device(db, current_user, device_id)

    start = time.monotonic()

    try:
        adapter = create_device_adapter(device)
        await adapter.connect()
        healthy = await adapter.health_check()
        await adapter.disconnect()

        latency_ms = round((time.monotonic() - start) * 1000, 2)

        if not healthy:
            return {"success": False, "error": "Device health check failed"}

        return {"success": True, "latency_ms": latency_ms}
    except Exception as error:
        return {"success": False, "error": str(error)}
