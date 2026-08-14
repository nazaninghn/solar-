"""STEP 52: Disaster Recovery API (Admin). Extended in STEP 83 with the
writers that were missing: targets could only ever be listed (never
seeded), and a drill could only be completed, never started."""

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
from app.modules.disaster_recovery.schemas import (
    CheckChecklistItemRequest,
    RecordEventRequest,
    StartDrillRequest,
)
from app.modules.disaster_recovery.service import (
    check_checklist_item,
    seed_recovery_targets,
    start_drill,
)
from app.modules.disaster_recovery.service import (
    complete_drill as complete_drill_service,
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


@router.post("/targets/refresh")
def refresh_recovery_targets(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """83: idempotent — seeds the 6 documented targets if missing,
    leaves any already-present row untouched."""
    return seed_recovery_targets(db)


@router.get("/drills")
def list_drills(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """52.43: DR drill history."""
    return db.query(RecoveryDrill).order_by(RecoveryDrill.created_at.desc()).limit(20).all()


@router.post("/drills")
def create_drill(
    data: StartDrillRequest,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """83: starts a drill and auto-seeds the same 12-item checklist
    from docs/operations/disaster-recovery.md — turns the documented
    manual quarterly/annual drill process into recorded data instead
    of only ever living in a doc nobody re-reads afterward."""
    return start_drill(
        db,
        scenario=data.scenario,
        target_service=data.target_service,
        environment=data.environment,
        executed_by=admin.email,
    )


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


@router.post("/drills/{drill_id}/checklist/{item_id}/check")
def check_drill_checklist_item(
    drill_id: int,
    item_id: int,
    data: CheckChecklistItemRequest,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """83: records who actually verified each of the 12 checklist
    items during a drill, and when — the doc's checklist was a list to
    tick by hand with nothing storing that it happened."""
    item = check_checklist_item(
        db, drill_id=drill_id, item_id=item_id, checked_by=admin.email, notes=data.notes
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Checklist item not found for this drill.")
    return item


@router.post("/drills/{drill_id}/events")
def record_drill_event(
    drill_id: int,
    data: RecordEventRequest,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """83: timeline entries during a drill (or a real incident, via
    drill_id left null) — this is what 52.35's RecoveryEvent table was
    built for but nothing ever wrote to."""
    drill = db.get(RecoveryDrill, drill_id)
    if drill is None:
        raise HTTPException(status_code=404, detail="Drill not found.")

    now = datetime.now(timezone.utc)
    event = RecoveryEvent(
        drill_id=drill_id,
        event_type=data.event_type,
        description=data.description,
        actor=admin.email,
        timestamp=now,
        created_at=now,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/drills/{drill_id}/complete")
def complete_drill(
    drill_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """83 fix: previously always evaluated every drill against the
    'database' target regardless of what it actually tested, and never
    computed total_recovery_minutes if the caller didn't supply it —
    meaning rto_met/rpo_met silently stayed null for every drill ever
    completed through this endpoint. Now derives duration from
    started_at/completed_at and evaluates against the drill's own
    target_service."""
    drill = complete_drill_service(db, drill_id)
    if drill is None:
        raise HTTPException(status_code=404, detail="Drill not found.")
    return drill
