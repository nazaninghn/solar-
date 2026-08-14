"""STEP 52: Disaster Recovery API (Admin)."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.modules.disaster_recovery.models import (
    RecoveryChecklist,
    RecoveryDrill,
    RecoveryEvent,
    RecoveryTarget,
)

router = APIRouter(prefix="/api/v1/admin/disaster-recovery", tags=["Disaster Recovery"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("SUPER_ADMIN", "COMPANY_ADMIN"):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@router.get("/targets")
def list_recovery_targets(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """52.13: RPO/RTO targets per service."""
    return db.query(RecoveryTarget).all()


@router.get("/drills")
def list_drills(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """52.43: DR drill history."""
    return db.query(RecoveryDrill).order_by(RecoveryDrill.created_at.desc()).limit(20).all()


@router.get("/drills/{drill_id}")
def get_drill(
    drill_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    drill = db.query(RecoveryDrill).filter(RecoveryDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found.")
    return drill


@router.get("/drills/{drill_id}/timeline")
def drill_timeline(
    drill_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """52.35: Recovery timeline for a drill."""
    return (
        db.query(RecoveryEvent)
        .filter(RecoveryEvent.drill_id == drill_id)
        .order_by(RecoveryEvent.timestamp.asc())
        .all()
    )


@router.get("/drills/{drill_id}/checklist")
def drill_checklist(
    drill_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """52.51: Recovery checklist for a drill."""
    return (
        db.query(RecoveryChecklist)
        .filter(RecoveryChecklist.drill_id == drill_id)
        .all()
    )


@router.post("/drills/{drill_id}/complete")
def complete_drill(
    drill_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Mark drill as completed and evaluate results."""
    drill = db.query(RecoveryDrill).filter(RecoveryDrill.id == drill_id).first()
    if not drill:
        raise HTTPException(status_code=404, detail="Drill not found.")

    drill.status = "COMPLETED"
    drill.completed_at = datetime.now(timezone.utc)

    # Evaluate against targets
    if drill.total_recovery_minutes:
        target = db.query(RecoveryTarget).filter(RecoveryTarget.service == "database").first()
        if target:
            drill.rto_met = drill.total_recovery_minutes <= target.rto_minutes
            drill.rpo_met = (drill.data_loss_minutes or 0) <= target.rpo_minutes

    db.commit()
    db.refresh(drill)
    return drill
