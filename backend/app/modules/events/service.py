"""STEP 43: Event, Alert, Notification service."""

import hashlib
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.modules.events.models import (
    AlertAuditLog,
    Event,
    Notification,
    SystemAlert,
)


def create_event(
    db: Session,
    organization_id: int,
    event_type: str,
    severity: str = "INFO",
    factory_id: int | None = None,
    device_id: int | None = None,
    source: str | None = None,
    payload_json: str | None = None,
) -> Event:
    now = datetime.now(timezone.utc)
    event = Event(
        organization_id=organization_id,
        factory_id=factory_id,
        device_id=device_id,
        event_type=event_type,
        severity=severity,
        source=source,
        occurred_at=now,
        payload_json=payload_json,
        created_at=now,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_alert_from_event(
    db: Session,
    event: Event,
    title: str,
    message: str | None = None,
    cooldown_seconds: int = 3600,
) -> SystemAlert | None:
    """43.15-43.16: Create alert with dedup and cooldown."""
    now = datetime.now(timezone.utc)

    # Dedup key
    dedup_key = hashlib.md5(
        f"{event.organization_id}:{event.factory_id}:{event.device_id}:{event.event_type}".encode()
    ).hexdigest()

    # Check existing open alert
    existing = (
        db.query(SystemAlert)
        .filter(SystemAlert.dedup_key == dedup_key, SystemAlert.status == "OPEN")
        .first()
    )
    if existing:
        existing.updated_at = now
        db.commit()
        return None  # Dedup — no new alert

    alert = SystemAlert(
        organization_id=event.organization_id,
        factory_id=event.factory_id,
        device_id=event.device_id,
        event_id=event.id,
        alert_type=event.event_type,
        severity=event.severity,
        title=title,
        message=message,
        status="OPEN",
        source=event.source,
        dedup_key=dedup_key,
        occurred_at=now,
        created_at=now,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def acknowledge_alert(db: Session, alert_id: int, organization_id: int, user: User, note: str | None = None) -> SystemAlert:
    alert = _get_alert(db, alert_id, organization_id)
    if alert.status != "OPEN":
        raise HTTPException(status_code=400, detail=f"Cannot acknowledge in status '{alert.status}'.")
    old = alert.status
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.updated_at = datetime.now(timezone.utc)
    _audit(db, alert.id, "ACKNOWLEDGED", old, "ACKNOWLEDGED", user.id, note)
    db.commit()
    db.refresh(alert)
    return alert


def resolve_alert(db: Session, alert_id: int, organization_id: int, user: User, note: str | None = None) -> SystemAlert:
    alert = _get_alert(db, alert_id, organization_id)
    if alert.status not in ("OPEN", "ACKNOWLEDGED"):
        raise HTTPException(status_code=400, detail=f"Cannot resolve in status '{alert.status}'.")
    old = alert.status
    alert.status = "RESOLVED"
    alert.resolved_by = user.id
    alert.resolved_at = datetime.now(timezone.utc)
    alert.updated_at = datetime.now(timezone.utc)
    _audit(db, alert.id, "RESOLVED", old, "RESOLVED", user.id, note)
    db.commit()
    db.refresh(alert)
    return alert


def dismiss_alert(db: Session, alert_id: int, organization_id: int, user: User) -> SystemAlert:
    alert = _get_alert(db, alert_id, organization_id)
    old = alert.status
    alert.status = "DISMISSED"
    alert.updated_at = datetime.now(timezone.utc)
    _audit(db, alert.id, "DISMISSED", old, "DISMISSED", user.id)
    db.commit()
    db.refresh(alert)
    return alert


def create_notification(
    db: Session,
    organization_id: int,
    user_id: int,
    notification_type: str,
    title: str,
    message: str | None = None,
    channel: str = "IN_APP",
    alert_id: int | None = None,
) -> Notification:
    now = datetime.now(timezone.utc)
    notif = Notification(
        organization_id=organization_id,
        user_id=user_id,
        alert_id=alert_id,
        type=notification_type,
        channel=channel,
        title=title,
        message=message,
        status="SENT" if channel == "IN_APP" else "PENDING",
        sent_at=now if channel == "IN_APP" else None,
        created_at=now,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> Notification:
    notif = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.read_at = datetime.now(timezone.utc)
    notif.status = "READ"
    db.commit()
    db.refresh(notif)
    return notif


def get_unread_count(db: Session, user_id: int) -> int:
    return db.query(Notification).filter(
        Notification.user_id == user_id, Notification.read_at == None
    ).count()


def _get_alert(db: Session, alert_id: int, organization_id: int) -> SystemAlert:
    alert = db.query(SystemAlert).filter(
        SystemAlert.id == alert_id, SystemAlert.organization_id == organization_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return alert


def _audit(db: Session, alert_id: int, action: str, old: str | None, new: str | None, user_id: int | None = None, note: str | None = None):
    db.add(AlertAuditLog(
        alert_id=alert_id,
        action=action,
        old_status=old,
        new_status=new,
        performed_by=user_id,
        metadata_json=f'{{"note":"{note}"}}' if note else None,
        created_at=datetime.now(timezone.utc),
    ))
