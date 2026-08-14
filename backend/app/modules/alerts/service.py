"""STEP 40: Alert & Incident Service."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.modules.alerts.models import (
    ALERT_ACKNOWLEDGED,
    ALERT_OPEN,
    ALERT_RESOLVED,
    INC_OPEN,
    Alert,
    AlertComment,
    Incident,
)


def list_alerts(db: Session, factory_id: int, status: str | None = None) -> list[Alert]:
    query = db.query(Alert).filter(Alert.factory_id == factory_id)
    if status:
        query = query.filter(Alert.status == status)
    return query.order_by(Alert.created_at.desc()).limit(100).all()


def get_alert(db: Session, alert_id: int, factory_id: int) -> Alert:
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.factory_id == factory_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return alert


def acknowledge_alert(db: Session, alert_id: int, factory_id: int, user: User) -> Alert:
    alert = get_alert(db, alert_id, factory_id)
    if alert.status != ALERT_OPEN:
        raise HTTPException(status_code=400, detail=f"Cannot acknowledge in status '{alert.status}'.")
    alert.status = ALERT_ACKNOWLEDGED
    alert.acknowledged_by = user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert


def resolve_alert(db: Session, alert_id: int, factory_id: int, user: User, reason: str) -> Alert:
    alert = get_alert(db, alert_id, factory_id)
    if alert.status not in (ALERT_OPEN, ALERT_ACKNOWLEDGED):
        raise HTTPException(status_code=400, detail=f"Cannot resolve in status '{alert.status}'.")
    alert.status = ALERT_RESOLVED
    alert.resolved_by = user.id
    alert.resolved_at = datetime.now(timezone.utc)
    alert.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert


def add_comment(db: Session, alert_id: int, factory_id: int, user: User, comment_text: str) -> AlertComment:
    get_alert(db, alert_id, factory_id)  # Verify exists
    comment = AlertComment(
        alert_id=alert_id,
        user_id=user.id,
        comment=comment_text,
        created_at=datetime.now(timezone.utc),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_alert_summary(db: Session, factory_id: int) -> dict:
    alerts = db.query(Alert).filter(Alert.factory_id == factory_id, Alert.status.in_([ALERT_OPEN, ALERT_ACKNOWLEDGED])).all()
    incidents = db.query(Incident).filter(Incident.factory_id == factory_id, Incident.status == INC_OPEN).count()

    return {
        "total_open": len(alerts),
        "critical": sum(1 for a in alerts if a.severity == "CRITICAL"),
        "high": sum(1 for a in alerts if a.severity == "HIGH"),
        "medium": sum(1 for a in alerts if a.severity == "MEDIUM"),
        "unacknowledged": sum(1 for a in alerts if a.status == ALERT_OPEN),
        "active_incidents": incidents,
    }


def list_incidents(db: Session, factory_id: int) -> list[Incident]:
    return db.query(Incident).filter(Incident.factory_id == factory_id).order_by(Incident.created_at.desc()).limit(50).all()
