from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_ENERGY
from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.devices.auth import get_device_from_api_key
from app.devices.health import calculate_device_health_score
from app.devices.rate_limit import enforce_telemetry_rate_limit
from app.models.device import Device
from app.models.factory import Factory
from app.models.user import User
from app.modules.devices.schemas import (
    DeviceCreate,
    DeviceCreatedResponse,
    DeviceHealthResponse,
    DeviceKeyResponse,
    DeviceResponse,
    DeviceStatusResponse,
    DeviceUpdate,
    TelemetryIngestRequest,
    TelemetryIngestResponse,
    TestConnectionResponse,
)
from app.modules.devices.service import (
    create_device,
    delete_device,
    get_device_status,
    get_devices,
    get_owned_device,
    ingest_telemetry,
    regenerate_device_key,
    test_connection,
    update_device,
)

# Factory-scoped endpoints.
router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/devices",
    tags=["Devices"],
)


@router.get("", response_model=list[DeviceResponse])
def list_devices(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_devices(db=db, factory_id=factory.id)


@router.post("", response_model=DeviceCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_device_endpoint(
    data: DeviceCreate,
    factory: Factory = Depends(get_accessible_factory),
    _permission_check: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    device, raw_key = create_device(db=db, factory_id=factory.id, data=data)

    return DeviceCreatedResponse(
        **DeviceResponse.model_validate(device).model_dump(),
        device_key=raw_key,
    )


@router.get("/status", response_model=list[DeviceStatusResponse])
def device_status_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_device_status(db=db, factory_id=factory.id)


# Non-nested item endpoints, per 16.11 — ownership validated in the
# service layer via a join, same pattern as Step 14's
# PATCH /notifications/{id}/read.
device_router = APIRouter(
    prefix="/api/v1/devices",
    tags=["Devices"],
)


@device_router.get("/{device_id}", response_model=DeviceResponse)
def get_device_endpoint(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_owned_device(db=db, current_user=current_user, device_id=device_id)


@device_router.patch("/{device_id}", response_model=DeviceResponse)
def update_device_endpoint(
    device_id: int,
    data: DeviceUpdate,
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    return update_device(db=db, current_user=current_user, device_id=device_id, data=data)


@device_router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device_endpoint(
    device_id: int,
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    delete_device(db=db, current_user=current_user, device_id=device_id)


@device_router.get("/{device_id}/health", response_model=DeviceHealthResponse)
def get_device_health_endpoint(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """31.17, 31.21: 0-100 health score blending data freshness,
    status, and recent error rate."""
    device = get_owned_device(db=db, current_user=current_user, device_id=device_id)
    health = calculate_device_health_score(device)

    return DeviceHealthResponse(
        device_id=device.id,
        status=device.status,
        last_seen_at=device.last_seen_at,
        **health,
    )


@device_router.post("/{device_id}/test-connection", response_model=TestConnectionResponse)
async def test_connection_endpoint(
    device_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await test_connection(db=db, current_user=current_user, device_id=device_id)


@device_router.post("/{device_id}/regenerate-key", response_model=DeviceKeyResponse)
def regenerate_device_key_endpoint(
    device_id: int,
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    raw_key = regenerate_device_key(db=db, current_user=current_user, device_id=device_id)

    return DeviceKeyResponse(device_key=raw_key)


@device_router.post("/{device_id}/telemetry", response_model=TelemetryIngestResponse)
def ingest_telemetry_endpoint(
    device_id: int,
    data: TelemetryIngestRequest,
    db: Session = Depends(get_db),
    device: Device = Depends(get_device_from_api_key),
):
    # 26.15: device-key auth, not get_current_user — this is the one
    # endpoint in the module a device itself calls, not a logged-in user
    # managing devices.
    enforce_telemetry_rate_limit(device.id)

    try:
        reading, was_duplicate = ingest_telemetry(db=db, device=device, data=data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    return TelemetryIngestResponse(
        id=reading.id,
        recorded=not was_duplicate,
        duplicate=was_duplicate,
    )
