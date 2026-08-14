"""
STEP 38: Command Orchestration Service.

Handles command creation, approval, queuing, execution, verification, and cancellation.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.user import User
from app.modules.orchestrator.guards import check_stale_approval, run_pre_execution_guard
from app.modules.orchestrator.models import (
    CS_APPROVED,
    CS_CANCELLED,
    CS_COMPLETED,
    CS_EXPIRED,
    CS_FAILED,
    CS_PENDING,
    CS_QUEUED,
    CS_REJECTED,
    CS_SENT,
    CS_VERIFIED,
    PRI_SAFETY,
    Command,
    CommandAudit,
    CommandVerification,
    ControlLock,
    ControlSnapshot,
)


def create_command(
    db: Session,
    factory_id: int,
    device_id: int,
    command_type: str,
    payload: dict,
    user: User,
    recommendation_id: int | None = None,
    priority: str = "MEDIUM",
    scheduled_at: datetime | None = None,
    expires_at: datetime | None = None,
    trace_id: str | None = None,
) -> Command:
    """38.7: Create a new command. 77.12-77.14: trace_id defaults to a
    fresh one (unchanged behavior) but a caller inside an HTTP request
    should pass the request's own trace_id (request.state.trace_id,
    app/core/middleware.py) instead, so a command created while
    handling a request shows up under the same trace as the API call
    that triggered it."""
    # Verify device belongs to factory
    device = db.query(Device).filter(Device.id == device_id, Device.factory_id == factory_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in factory.")

    now = datetime.now(timezone.utc)
    idempotency_key = f"cmd-{factory_id}-{device_id}-{uuid.uuid4().hex[:12]}"
    trace_id = trace_id or f"trace-{uuid.uuid4().hex[:16]}"

    # Default expiration: 4 hours from now
    if not expires_at:
        expires_at = now + timedelta(hours=4)

    cmd = Command(
        factory_id=factory_id,
        device_id=device_id,
        recommendation_id=recommendation_id,
        type=command_type,
        payload_json=json.dumps(payload),
        status=CS_PENDING,
        priority=priority,
        scheduled_at=scheduled_at,
        expires_at=expires_at,
        created_by=user.id,
        idempotency_key=idempotency_key,
        trace_id=trace_id,
        created_at=now,
    )
    db.add(cmd)
    _audit(db, cmd, "CREATED", user.id, None, CS_PENDING)
    db.commit()
    db.refresh(cmd)
    return cmd


def approve_command(db: Session, command_id: int, factory_id: int, user: User) -> Command:
    """38.7: Approve a pending command."""
    cmd = _get_command(db, command_id, factory_id)
    if cmd.status != CS_PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot approve in status '{cmd.status}'.")

    old = cmd.status
    cmd.status = CS_APPROVED
    cmd.approved_by = user.id
    cmd.updated_at = datetime.now(timezone.utc)
    _audit(db, cmd, "APPROVED", user.id, old, CS_APPROVED)
    db.commit()
    db.refresh(cmd)
    return cmd


def queue_command(db: Session, command_id: int, factory_id: int) -> Command:
    """38.15: Move approved command to queue for execution."""
    cmd = _get_command(db, command_id, factory_id)
    if cmd.status != CS_APPROVED:
        raise HTTPException(status_code=400, detail=f"Cannot queue in status '{cmd.status}'.")

    # Stale approval check (38.12)
    if not check_stale_approval(cmd):
        cmd.status = CS_EXPIRED
        cmd.failure_reason = "Stale approval — conditions may have changed"
        _audit(db, cmd, "STALE_EXPIRED", None, CS_APPROVED, CS_EXPIRED)
        db.commit()
        raise HTTPException(status_code=409, detail="Approval expired. Re-approval needed.")

    # Pre-execution guard (38.11)
    device = db.query(Device).filter(Device.id == cmd.device_id).first()
    if not device:
        cmd.status = CS_FAILED
        cmd.failure_reason = "DEVICE_NOT_FOUND"
        db.commit()
        raise HTTPException(status_code=404, detail="Device not found.")

    passed, reason = run_pre_execution_guard(db, cmd, device)
    if not passed:
        cmd.status = CS_FAILED
        cmd.failure_reason = reason
        _audit(db, cmd, "GUARD_BLOCKED", None, CS_APPROVED, CS_FAILED, reason)
        db.commit()
        raise HTTPException(status_code=409, detail=f"Safety guard failed: {reason}")

    # Acquire lock (38.26)
    now = datetime.now(timezone.utc)
    lock = ControlLock(
        device_id=cmd.device_id,
        command_id=cmd.id,
        is_active=True,
        acquired_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    db.add(lock)

    # Snapshot (38.43)
    snapshot = ControlSnapshot(
        command_id=cmd.id,
        device_status=device.status,
        created_at=now,
    )
    db.add(snapshot)

    old = cmd.status
    cmd.status = CS_QUEUED
    cmd.updated_at = now
    _audit(db, cmd, "QUEUED", None, old, CS_QUEUED)
    db.commit()
    db.refresh(cmd)
    return cmd


def cancel_command(db: Session, command_id: int, factory_id: int, user: User, reason: str | None = None) -> Command:
    """38.7: Cancel a command."""
    cmd = _get_command(db, command_id, factory_id)
    if cmd.status in (CS_COMPLETED, CS_VERIFIED, CS_CANCELLED):
        raise HTTPException(status_code=400, detail=f"Cannot cancel in status '{cmd.status}'.")

    old = cmd.status
    cmd.status = CS_CANCELLED
    cmd.failure_reason = reason or "Cancelled by user"
    cmd.updated_at = datetime.now(timezone.utc)
    _audit(db, cmd, "CANCELLED", user.id, old, CS_CANCELLED, reason)

    # Release lock
    _release_lock(db, cmd.id)
    db.commit()
    db.refresh(cmd)
    return cmd


def emergency_stop(db: Session, factory_id: int, user: User, reason: str) -> list[Command]:
    """38.24: Emergency stop — cancel all active commands for factory."""
    now = datetime.now(timezone.utc)
    active = (
        db.query(Command)
        .filter(
            Command.factory_id == factory_id,
            Command.status.in_([CS_QUEUED, CS_SENT, CS_APPROVED]),
        )
        .all()
    )

    stopped = []
    for cmd in active:
        old = cmd.status
        cmd.status = CS_CANCELLED
        cmd.failure_reason = f"EMERGENCY_STOP: {reason}"
        cmd.updated_at = now
        _audit(db, cmd, "EMERGENCY_STOP", user.id, old, CS_CANCELLED, reason)
        _release_lock(db, cmd.id)
        stopped.append(cmd)

    db.commit()
    return stopped


def get_control_status(db: Session, factory_id: int) -> dict:
    """38.34: Control center status."""
    from datetime import date
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    cmds = db.query(Command).filter(Command.factory_id == factory_id).all()

    return {
        "factory_id": factory_id,
        "active_commands": sum(1 for c in cmds if c.status in (CS_QUEUED, CS_SENT)),
        "queued_commands": sum(1 for c in cmds if c.status == CS_QUEUED),
        "executing_commands": sum(1 for c in cmds if c.status == CS_SENT),
        "failed_today": sum(1 for c in cmds if c.status == CS_FAILED and c.updated_at and c.updated_at >= today_start),
        "verified_today": sum(1 for c in cmds if c.status == CS_VERIFIED and c.verified_at and c.verified_at >= today_start),
        "emergency_stop_active": False,  # Would check a factory-level flag
    }


def list_commands(db: Session, factory_id: int, limit: int = 50) -> list[Command]:
    return (
        db.query(Command)
        .filter(Command.factory_id == factory_id)
        .order_by(Command.created_at.desc())
        .limit(limit)
        .all()
    )


def _get_command(db: Session, command_id: int, factory_id: int) -> Command:
    cmd = db.query(Command).filter(Command.id == command_id, Command.factory_id == factory_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found.")
    return cmd


def _audit(db: Session, cmd: Command, action: str, user_id: int | None, old: str | None, new: str | None, reason: str | None = None):
    db.add(CommandAudit(
        command_id=cmd.id,
        action=action,
        user_id=user_id,
        old_status=old,
        new_status=new,
        reason=reason,
        created_at=datetime.now(timezone.utc),
    ))


def _release_lock(db: Session, command_id: int):
    lock = db.query(ControlLock).filter(ControlLock.command_id == command_id, ControlLock.is_active == True).first()
    if lock:
        lock.is_active = False
        lock.released_at = datetime.now(timezone.utc)
