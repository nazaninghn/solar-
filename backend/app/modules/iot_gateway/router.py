"""STEP 39.25/39.32-39.33: IoT Gateway API."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_ENERGY
from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.iot_gateway.models import DeadLetterQueue, Gateway
from app.modules.iot_gateway.schemas import (
    DLQEntryResponse,
    GatewayHealthResponse,
    GatewayRegisterRequest,
    GatewayResponse,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["IoT Gateway"],
)


@router.get("/factories/{factory_id}/gateways", response_model=list[GatewayResponse])
def list_gateways(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return db.query(Gateway).filter(Gateway.factory_id == factory.id).all()


@router.post("/gateways/register", response_model=GatewayResponse, status_code=201)
def register_gateway(
    data: GatewayRegisterRequest,
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """39.25: Register a new gateway."""
    existing = db.query(Gateway).filter(Gateway.gateway_id == data.gateway_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Gateway already registered.")

    gateway = Gateway(
        factory_id=data.factory_id,
        gateway_id=data.gateway_id,
        name=data.name,
        serial_number=data.serial_number,
        firmware_version=data.firmware_version,
        status="PROVISIONING",
        created_at=datetime.now(timezone.utc),
    )
    db.add(gateway)
    db.commit()
    db.refresh(gateway)
    return gateway


@router.get("/gateways/{gateway_id}/health", response_model=GatewayHealthResponse)
def gateway_health(
    gateway_id: str,
    db: Session = Depends(get_db),
):
    """39.32: Gateway health status."""
    gw = db.query(Gateway).filter(Gateway.gateway_id == gateway_id).first()
    if not gw:
        raise HTTPException(status_code=404, detail="Gateway not found.")

    return GatewayHealthResponse(
        gateway_id=gw.gateway_id,
        status=gw.status,
        uptime_seconds=gw.uptime_seconds,
        connected_devices=gw.connected_devices,
        last_seen_at=gw.last_seen_at,
        mqtt_status="CONNECTED" if gw.status == "ONLINE" else "DISCONNECTED",
        signal_quality=gw.signal_quality,
    )


@router.get("/factories/{factory_id}/dlq", response_model=list[DLQEntryResponse])
def list_dead_letter_queue(
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """39.23: View dead letter queue entries."""
    return (
        db.query(DeadLetterQueue)
        .filter(DeadLetterQueue.factory_id == factory.id)
        .order_by(DeadLetterQueue.created_at.desc())
        .limit(50)
        .all()
    )
