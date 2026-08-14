"""
STEP 32.23-32.24: Energy Control API Router.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_ENERGY
from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.control.schemas import (
    ActionCreateRequest,
    ActionResponse,
    ActionSummaryResponse,
)
from app.modules.control.service import (
    approve_action,
    cancel_action,
    create_action,
    execute_action,
    get_action,
    get_action_summary,
    list_actions,
    reject_action,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/actions",
    tags=["Energy Control"],
)


@router.get("", response_model=list[ActionResponse])
def list_actions_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """List all energy actions for a factory."""
    return list_actions(db=db, factory_id=factory.id)


@router.get("/summary", response_model=ActionSummaryResponse)
def action_summary_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """32.27: Control dashboard summary."""
    return get_action_summary(db=db, factory_id=factory.id)


@router.post("", response_model=ActionResponse, status_code=201)
def create_action_endpoint(
    data: ActionCreateRequest,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """32.4: Create a new energy action (PENDING)."""
    return create_action(
        db=db, factory_id=factory.id, data=data, current_user=current_user
    )


@router.get("/{action_id}", response_model=ActionResponse)
def get_action_endpoint(
    action_id: int,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """Get a single action detail."""
    return get_action(db=db, factory_id=factory.id, action_id=action_id)


@router.post("/{action_id}/approve", response_model=ActionResponse)
def approve_action_endpoint(
    action_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """32.8: Approve an action with safety check."""
    return approve_action(
        db=db, factory_id=factory.id, action_id=action_id, current_user=current_user
    )


@router.post("/{action_id}/reject", response_model=ActionResponse)
def reject_action_endpoint(
    action_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """32.8: Reject an action."""
    return reject_action(
        db=db, factory_id=factory.id, action_id=action_id, current_user=current_user
    )


@router.post("/{action_id}/cancel", response_model=ActionResponse)
def cancel_action_endpoint(
    action_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """32.21: Cancel an action."""
    return cancel_action(
        db=db, factory_id=factory.id, action_id=action_id, current_user=current_user
    )


@router.post("/{action_id}/execute", response_model=ActionResponse)
def execute_action_endpoint(
    action_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    """32.14: Execute an approved action — creates command and marks as RUNNING."""
    return execute_action(
        db=db, factory_id=factory.id, action_id=action_id, current_user=current_user
    )
