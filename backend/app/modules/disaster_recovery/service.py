"""
STEP 83: operationalizes the DR schema built in Step 52 — real RPO/RTO
targets, and a way to actually create/run/complete a drill instead of
only ever reading an empty table. The quarterly/annual restore drills
this project runs are manual (docs/operations/disaster-recovery.md) —
there's no isolated recovery environment or Render API access to
automate an actual restore-and-verify. What this DOES do honestly is
turn that manual process into recorded data: start a drill, check off
the same 12 checklist items a human works through by hand, log the
timeline, and compute real RTO/RPO from the timestamps actually
recorded — instead of the numbers only ever living in someone's memory
or a doc nobody re-reads after the drill.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.disaster_recovery.models import (
    RecoveryChecklist,
    RecoveryDrill,
    RecoveryEvent,
    RecoveryTarget,
)

# 83: transcribed exactly from docs/operations/disaster-recovery.md's
# "Recovery Objectives" table — one definition of these numbers, not
# two that can drift apart.
RECOVERY_TARGETS = [
    {"service": "API", "rpo_minutes": 15, "rto_minutes": 30, "priority": "CRITICAL"},
    {"service": "Database", "rpo_minutes": 60, "rto_minutes": 60, "priority": "CRITICAL"},
    {"service": "Telemetry", "rpo_minutes": 60, "rto_minutes": 120, "priority": "HIGH"},
    {"service": "Billing", "rpo_minutes": 15, "rto_minutes": 60, "priority": "CRITICAL"},
    {"service": "Analytics", "rpo_minutes": 240, "rto_minutes": 240, "priority": "MEDIUM"},
    {"service": "Reports", "rpo_minutes": 1440, "rto_minutes": 480, "priority": "LOW"},
]

# 83: transcribed exactly from the doc's "Recovery Drill Checklist".
RECOVERY_DRILL_CHECKLIST_ITEMS = [
    "Select backup to restore",
    "Restore to separate environment",
    "Verify database schema complete",
    "Verify critical tables have data",
    "Start application against restored DB",
    "Run health checks",
    "Login as test user",
    "Verify dashboard loads",
    "Record RTO (time taken)",
    "Record RPO (data freshness)",
    "Document issues found",
    "Update recovery plan if needed",
]


def seed_recovery_targets(db: Session) -> list[RecoveryTarget]:
    """83: idempotent upsert, same shape as Step 81's seed_model_registry
    — safe to run repeatedly (e.g. from a daily job) without creating
    duplicates or clobbering a value an admin has since adjusted."""
    seeded = []

    for definition in RECOVERY_TARGETS:
        target = db.scalar(
            select(RecoveryTarget).where(RecoveryTarget.service == definition["service"])
        )
        now = datetime.now(timezone.utc)

        if target is None:
            target = RecoveryTarget(
                service=definition["service"],
                rpo_minutes=definition["rpo_minutes"],
                rto_minutes=definition["rto_minutes"],
                priority=definition["priority"],
                notes="Seeded from docs/operations/disaster-recovery.md",
                created_at=now,
            )
            db.add(target)
        # An existing row is left alone even if the doc's numbers
        # change later — an admin may have deliberately tightened a
        # target after a real incident, and a blind re-seed shouldn't
        # silently revert that.

    db.commit()
    seeded = db.scalars(select(RecoveryTarget)).all()
    return list(seeded)


def start_drill(
    db: Session,
    scenario: str,
    target_service: str,
    environment: str,
    executed_by: str,
) -> RecoveryDrill:
    now = datetime.now(timezone.utc)

    drill = RecoveryDrill(
        scenario=scenario,
        target_service=target_service,
        environment=environment,
        status="IN_PROGRESS",
        started_at=now,
        executed_by=executed_by,
        created_at=now,
    )
    db.add(drill)
    db.flush()

    for item in RECOVERY_DRILL_CHECKLIST_ITEMS:
        db.add(RecoveryChecklist(drill_id=drill.id, item=item))

    db.add(
        RecoveryEvent(
            drill_id=drill.id,
            event_type="DRILL_STARTED",
            description=f"Drill started for scenario: {scenario}",
            actor=executed_by,
            timestamp=now,
            created_at=now,
        )
    )

    db.commit()
    db.refresh(drill)
    return drill


def complete_drill(db: Session, drill_id: int) -> RecoveryDrill | None:
    """83 fix: previously always evaluated against the 'database' target
    regardless of what the drill actually tested — a Billing-scenario
    drill was silently checked against Database's RTO/RPO. Now looks up
    RecoveryTarget by the drill's own target_service."""
    drill = db.get(RecoveryDrill, drill_id)
    if drill is None:
        return None

    now = datetime.now(timezone.utc)
    drill.status = "COMPLETED"
    drill.completed_at = now

    if drill.started_at is not None and drill.total_recovery_minutes is None:
        drill.total_recovery_minutes = (now - drill.started_at).total_seconds() / 60.0

    target = db.scalar(
        select(RecoveryTarget).where(RecoveryTarget.service == drill.target_service)
    )
    if target and drill.total_recovery_minutes is not None:
        drill.rto_met = drill.total_recovery_minutes <= target.rto_minutes
        drill.rpo_met = (drill.data_loss_minutes or 0) <= target.rpo_minutes

    db.add(
        RecoveryEvent(
            drill_id=drill.id,
            event_type="DRILL_COMPLETED",
            description=(
                f"Drill completed in {drill.total_recovery_minutes:.1f} min"
                if drill.total_recovery_minutes is not None
                else "Drill completed"
            ),
            timestamp=now,
            created_at=now,
        )
    )

    db.commit()
    db.refresh(drill)
    return drill


def check_checklist_item(
    db: Session,
    drill_id: int,
    item_id: int,
    checked_by: str,
    notes: str | None = None,
) -> RecoveryChecklist | None:
    item = db.scalar(
        select(RecoveryChecklist).where(
            RecoveryChecklist.id == item_id,
            RecoveryChecklist.drill_id == drill_id,
        )
    )
    if item is None:
        return None

    item.checked = True
    item.checked_by = checked_by
    item.checked_at = datetime.now(timezone.utc)
    if notes:
        item.notes = notes

    db.commit()
    db.refresh(item)
    return item
