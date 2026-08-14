"""STEP 38.33-38.34: Control Center API."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_ENERGY
from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.orchestrator.schemas import (
    CommandCreateRequest,
    CommandResponse,
    ControlStatusResponse,
    EmergencyStopRequest,
)
from app.modules.orchestrator.service import (
    approve_command,
    cancel_command,
    create_command,
    emergency_stop,
    get_control_status,
    list_commands,
    queue_command,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/control",
    tags=["Control Center"],
)


@router.get("/status", response_model=ControlStatusResponse)
def control_status(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """38.34: Control center status overview."""
    return get_control_status(db=db, factory_id=factory.id)


@router.get("/commands", response_model=list[CommandResponse])
def get_commands(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """38.34: List recent commands."""
    return list_commands(db=db, factory_id=factory.id)


@router.post("/commands", response_model=CommandResponse, status_code=201)
def create_command_endpoint(
    data: CommandCreateRequest,
    request: Request,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """38.33: Create a new command."""
    return create_command(
        db=db,
        factory_id=factory.id,
        device_id=data.device_id,
        command_type=data.type,
        payload=data.payload,
        user=current_user,
        recommendation_id=data.recommendation_id,
        priority=data.priority,
        scheduled_at=data.scheduled_at,
        expires_at=data.expires_at,
        trace_id=getattr(request.state, "trace_id", None),
    )


@router.post("/commands/{command_id}/approve", response_model=CommandResponse)
def approve_command_endpoint(
    command_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """38.33: Approve a command."""
    return approve_command(db=db, command_id=command_id, factory_id=factory.id, user=current_user)


@router.post("/commands/{command_id}/execute", response_model=CommandResponse)
def execute_command_endpoint(
    command_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """38.33: Queue an approved command for execution."""
    return queue_command(db=db, command_id=command_id, factory_id=factory.id)


@router.post("/commands/{command_id}/cancel", response_model=CommandResponse)
def cancel_command_endpoint(
    command_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """38.33: Cancel a command."""
    return cancel_command(db=db, command_id=command_id, factory_id=factory.id, user=current_user)


@router.post("/emergency-stop", response_model=list[CommandResponse])
def emergency_stop_endpoint(
    data: EmergencyStopRequest,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """38.24: Emergency stop — cancel all active commands."""
    return emergency_stop(db=db, factory_id=factory.id, user=current_user, reason=data.reason)
