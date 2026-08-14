"""STEP 47: Security monitoring API for admins."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.modules.security.models import BackupRecord, DisasterRecoveryPlan, SecurityEvent

router = APIRouter(prefix="/api/v1/admin/security", tags=["Security"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    from fastapi import HTTPException
    if current_user.role not in ("SUPER_ADMIN", "COMPANY_ADMIN"):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@router.get("/events")
def list_security_events(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
):
    """47.33: Security events list."""
    query = db.query(SecurityEvent)
    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    return query.order_by(SecurityEvent.created_at.desc()).limit(limit).all()


@router.get("/events/summary")
def security_summary(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """47.38: Security dashboard summary."""
    from datetime import datetime, timedelta, timezone
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    events = db.query(SecurityEvent).filter(SecurityEvent.created_at >= last_24h).all()

    return {
        "total_events_24h": len(events),
        "failed_logins": sum(1 for e in events if e.event_type == "LOGIN_FAILED"),
        "account_lockouts": sum(1 for e in events if e.event_type == "ACCOUNT_LOCKED"),
        "rate_limit_hits": sum(1 for e in events if e.event_type == "RATE_LIMIT_EXCEEDED"),
        "suspicious_requests": sum(1 for e in events if e.event_type == "SUSPICIOUS_REQUEST"),
        "token_reuse": sum(1 for e in events if e.event_type == "TOKEN_REUSE"),
    }


@router.get("/backups")
def list_backups(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """47.35: Backup history."""
    return db.query(BackupRecord).order_by(BackupRecord.started_at.desc()).limit(30).all()


@router.get("/disaster-recovery")
def list_dr_plans(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """47.41: DR plans and test results."""
    return db.query(DisasterRecoveryPlan).all()
