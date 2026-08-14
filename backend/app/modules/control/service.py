"""
STEP 32: Energy Control Service.

Handles action creation, approval, execution, cancellation, and verification.
"""

import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.user import User
from app.modules.control.models import (
    ALLOWED_ACTION_TYPES,
    CMD_PENDING,
    STATUS_APPROVED,
    STATUS_BLOCKED,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_REJECTED,
    STATUS_RUNNING,
    STATUS_SCHEDULED,
    STATUS_VERIFYING,
    CommandQueue,
    EnergyAction,
)
from app.modules.control.safety import run_safety_checks
from app.modules.control.schemas import ActionCreateRequest


def create_action(
    db: Session,
    factory_id: int,
    data: ActionCreateRequest,
    current_user: User,
) -> EnergyAction:
    """32.4: Create a new energy action (PENDING status)."""
    if data.type not in ALLOWED_ACTION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action type '{data.type}' is not allowed. Allowed: {ALLOWED_ACTION_TYPES}",
        )

    # Verify device belongs to factory
    device = db.query(Device).filter(
        Device.id == data.device_id,
        Device.factory_id == factory_id,
    ).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found in this factory.",
        )

    action = EnergyAction(
        factory_id=factory_id,
        recommendation_id=data.recommendation_id,
        device_id=data.device_id,
        type=data.type,
        status=STATUS_PENDING,
        scheduled_start=data.scheduled_start,
        scheduled_end=data.scheduled_end,
        target_power_kw=data.target_power_kw,
        target_energy_kwh=data.target_energy_kwh,
        target_soc=data.target_soc,
        created_by=current_user.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def get_action(db: Session, factory_id: int, action_id: int) -> EnergyAction:
    """Get a single action by ID, scoped to factory."""
    action = db.query(EnergyAction).filter(
        EnergyAction.id == action_id,
        EnergyAction.factory_id == factory_id,
    ).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found.")
    return action


def list_actions(db: Session, factory_id: int) -> list[EnergyAction]:
    """List all actions for a factory, newest first."""
    return (
        db.query(EnergyAction)
        .filter(EnergyAction.factory_id == factory_id)
        .order_by(EnergyAction.created_at.desc())
        .limit(100)
        .all()
    )


def approve_action(
    db: Session,
    factory_id: int,
    action_id: int,
    current_user: User,
) -> EnergyAction:
    """32.8: Approve an action — runs safety checks before approval."""
    action = get_action(db, factory_id, action_id)

    if action.status != STATUS_PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve action in status '{action.status}'. Must be PENDING.",
        )

    # Run safety checks
    device = db.query(Device).filter(Device.id == action.device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    safety_result = run_safety_checks(db=db, action=action, device=device)

    if not safety_result.passed:
        action.status = STATUS_BLOCKED
        action.failure_reason = f"Safety blocked: {safety_result.blocked_reason}"
        db.commit()
        db.refresh(action)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Action blocked by safety engine: {safety_result.blocked_reason}",
        )

    now = datetime.now(timezone.utc)
    action.status = STATUS_APPROVED
    action.approved_by = current_user.id
    action.approved_at = now

    # If scheduled in the future, mark as SCHEDULED; otherwise ready to execute
    if action.scheduled_start and action.scheduled_start > now:
        action.status = STATUS_SCHEDULED
    else:
        action.status = STATUS_APPROVED

    db.commit()
    db.refresh(action)
    return action


def reject_action(
    db: Session,
    factory_id: int,
    action_id: int,
    current_user: User,
    reason: str | None = None,
) -> EnergyAction:
    """32.8: Reject an action."""
    action = get_action(db, factory_id, action_id)

    if action.status not in (STATUS_PENDING, STATUS_SCHEDULED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject action in status '{action.status}'.",
        )

    action.status = STATUS_REJECTED
    action.failure_reason = reason or "Rejected by user."
    db.commit()
    db.refresh(action)
    return action


def cancel_action(
    db: Session,
    factory_id: int,
    action_id: int,
    current_user: User,
) -> EnergyAction:
    """32.21: Cancel a pending/scheduled/approved action."""
    action = get_action(db, factory_id, action_id)

    if action.status in (STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel action in status '{action.status}'.",
        )

    action.status = STATUS_CANCELLED
    action.failure_reason = f"Cancelled by user {current_user.id}"
    db.commit()
    db.refresh(action)
    return action


def execute_action(
    db: Session,
    factory_id: int,
    action_id: int,
    current_user: User,
) -> EnergyAction:
    """
    32.14-32.17: Execute an approved action.
    - Revalidates safety (32.19)
    - Creates command in queue
    - Marks action as RUNNING
    """
    action = get_action(db, factory_id, action_id)

    if action.status not in (STATUS_APPROVED, STATUS_SCHEDULED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot execute action in status '{action.status}'. Must be APPROVED or SCHEDULED.",
        )

    # 32.19: Revalidate safety before execution
    device = db.query(Device).filter(Device.id == action.device_id).first()
    if not device:
        action.status = STATUS_FAILED
        action.failure_reason = "Device not found at execution time."
        db.commit()
        db.refresh(action)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    safety_result = run_safety_checks(db=db, action=action, device=device)
    if not safety_result.passed:
        action.status = STATUS_BLOCKED
        action.failure_reason = f"Revalidation failed: {safety_result.blocked_reason}"
        db.commit()
        db.refresh(action)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Safety revalidation failed: {safety_result.blocked_reason}",
        )

    # 32.13-32.14: Create command in queue
    idempotency_key = f"factory-{factory_id}-action-{action.id}-cmd-{uuid.uuid4().hex[:8]}"

    command_type = "SET_CHARGE_POWER" if action.type == "CHARGE_BATTERY" else "SET_DISCHARGE_POWER"
    payload = {"power_kw": action.target_power_kw or 0}

    command = CommandQueue(
        action_id=action.id,
        device_id=device.id,
        command_type=command_type,
        payload_json=json.dumps(payload),
        status=CMD_PENDING,
        idempotency_key=idempotency_key,
        created_at=datetime.now(timezone.utc),
        scheduled_at=action.scheduled_start,
    )
    db.add(command)

    # Update action status
    action.status = STATUS_RUNNING
    action.started_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(action)
    return action


def get_action_summary(db: Session, factory_id: int) -> dict:
    """32.27: Summary counts for control dashboard."""
    from datetime import date

    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    actions = db.query(EnergyAction).filter(EnergyAction.factory_id == factory_id).all()

    active = sum(1 for a in actions if a.status in (STATUS_RUNNING, STATUS_VERIFYING))
    scheduled = sum(1 for a in actions if a.status == STATUS_SCHEDULED)
    completed_today = sum(
        1 for a in actions
        if a.status == STATUS_COMPLETED and a.completed_at and a.completed_at >= today_start
    )
    failed_today = sum(
        1 for a in actions
        if a.status == STATUS_FAILED and a.completed_at and a.completed_at >= today_start
    )

    return {
        "active": active,
        "scheduled": scheduled,
        "completed_today": completed_today,
        "failed_today": failed_today,
    }
