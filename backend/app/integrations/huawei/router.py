"""
Huawei FusionSolar integration API endpoints.

Allows customers to connect their Huawei inverter accounts
to SolarFlow for real-time data pulling.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.integrations.huawei.client import (
    FUSIONSOLAR_EU_URL,
    FUSIONSOLAR_INTL_URL,
    HuaweiFusionSolarClient,
)
from app.integrations.huawei.sync_service import sync_station_data
from app.models.factory import Factory
from app.models.user import User
from app.modules.devices.connection_config import get_connection_config, set_connection_config
from app.models.device import Device

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/integrations/huawei",
    tags=["Integrations — Huawei"],
)


# ─── Schemas ──────────────────────────────────────────────────────


class HuaweiConnectRequest(BaseModel):
    username: str
    password: str
    region: str = "international"  # "international" or "europe"


class HuaweiConnectResponse(BaseModel):
    success: bool
    message: str
    stations: list[dict] = []


class HuaweiSyncResponse(BaseModel):
    success: bool
    message: str
    readings_synced: int = 0


class HuaweiStatusResponse(BaseModel):
    connected: bool
    username: str | None = None
    station_code: str | None = None
    station_name: str | None = None
    last_sync: str | None = None


# ─── Endpoints ────────────────────────────────────────────────────


@router.post("/connect", response_model=HuaweiConnectResponse)
async def connect_huawei(
    data: HuaweiConnectRequest,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Connect a Huawei FusionSolar account to a factory.
    Tests credentials, then stores them encrypted for automatic sync.
    """
    base_url = FUSIONSOLAR_EU_URL if data.region == "europe" else FUSIONSOLAR_INTL_URL

    client = HuaweiFusionSolarClient(
        username=data.username,
        password=data.password,
        base_url=base_url,
    )

    result = await client.test_connection()

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not connect to FusionSolar: {result['error']}",
        )

    # Store credentials encrypted on a "virtual" device representing
    # the Huawei integration for this factory.
    device = _get_or_create_huawei_device(db, factory.id)

    set_connection_config(db, device, {
        "provider": "huawei_fusionsolar",
        "username": data.username,
        "password": data.password,
        "base_url": base_url,
        "station_code": result["stations"][0]["code"] if result["stations"] else None,
        "station_name": result["stations"][0]["name"] if result["stations"] else None,
    })

    return HuaweiConnectResponse(
        success=True,
        message=f"Connected successfully. Found {result['stations_count']} station(s).",
        stations=result["stations"],
    )


@router.get("/status", response_model=HuaweiStatusResponse)
def huawei_status(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """Check if Huawei integration is configured for this factory."""
    device = _find_huawei_device(db, factory.id)

    if not device:
        return HuaweiStatusResponse(connected=False)

    config = get_connection_config(db, device)
    if not config:
        return HuaweiStatusResponse(connected=False)

    return HuaweiStatusResponse(
        connected=True,
        username=config.get("username"),
        station_code=config.get("station_code"),
        station_name=config.get("station_name"),
        last_sync=device.last_seen_at.isoformat() if device.last_seen_at else None,
    )


@router.post("/sync", response_model=HuaweiSyncResponse)
async def sync_huawei(
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger a data sync from Huawei FusionSolar."""
    device = _find_huawei_device(db, factory.id)

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Huawei integration not configured. Call /connect first.",
        )

    config = get_connection_config(db, device)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stored credentials found.",
        )

    count = await sync_station_data(db, device, config)

    return HuaweiSyncResponse(
        success=True,
        message=f"Synced {count} reading(s) from FusionSolar.",
        readings_synced=count,
    )


@router.delete("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_huawei(
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove Huawei integration from this factory."""
    device = _find_huawei_device(db, factory.id)
    if device:
        device.connection_config_encrypted = None
        device.status = "OFFLINE"
        db.commit()


# ─── Helpers ──────────────────────────────────────────────────────


def _find_huawei_device(db: Session, factory_id: int) -> Device | None:
    from sqlalchemy import select

    return db.scalar(
        select(Device).where(
            Device.factory_id == factory_id,
            Device.device_type == "HUAWEI_INTEGRATION",
        )
    )


def _get_or_create_huawei_device(db: Session, factory_id: int) -> Device:
    device = _find_huawei_device(db, factory_id)
    if device:
        return device

    from datetime import datetime, timezone

    device = Device(
        factory_id=factory_id,
        name="Huawei FusionSolar",
        device_type="HUAWEI_INTEGRATION",
        manufacturer="Huawei",
        model="FusionSolar Cloud",
        connection_type="API",
        device_key_hash="integration-no-key",
        status="ONLINE",
        created_at=datetime.now(timezone.utc),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device
