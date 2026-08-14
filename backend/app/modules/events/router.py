"""STEP 43.30-43.31: Events, Alerts & Notifications API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.modules.events.models import Notification, SystemAlert
from app.modules.events.schemas import (
    AcknowledgeRequest,
    NotificationResponse,
    ResolveRequest,
    SystemAlertResponse,
    UnreadCountResponse,
)
from app.modules.events.service import (
    acknowledge_alert,
    dismiss_alert,
    get_unread_count,
    mark_notification_read,
    resolve_alert,
)

# Alert API (43.31)
alert_router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts (Step 43)"])


@alert_router.get("", response_model=list[SystemAlertResponse])
def list_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    query = db.query(SystemAlert).filter(SystemAlert.organization_id == current_user.organization_id)
    if severity:
        query = query.filter(SystemAlert.severity == severity)
    if status:
        query = query.filter(SystemAlert.status == status)
    return query.order_by(SystemAlert.created_at.desc()).limit(limit).all()


@alert_router.get("/{alert_id}", response_model=SystemAlertResponse)
def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.query(SystemAlert).filter(
        SystemAlert.id == alert_id, SystemAlert.organization_id == current_user.organization_id
    ).first()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found.")
    return alert


@alert_router.post("/{alert_id}/acknowledge", response_model=SystemAlertResponse)
def acknowledge_endpoint(
    alert_id: int,
    data: AcknowledgeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return acknowledge_alert(db, alert_id, current_user.organization_id, current_user, data.note)


@alert_router.post("/{alert_id}/resolve", response_model=SystemAlertResponse)
def resolve_endpoint(
    alert_id: int,
    data: ResolveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return resolve_alert(db, alert_id, current_user.organization_id, current_user, data.note)


@alert_router.post("/{alert_id}/dismiss", response_model=SystemAlertResponse)
def dismiss_endpoint(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return dismiss_alert(db, alert_id, current_user.organization_id, current_user)


# Notification API (43.30)
notif_router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications (Step 43)"])


@notif_router.get("", response_model=list[NotificationResponse])
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=200),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


@notif_router.get("/unread", response_model=list[NotificationResponse])
def list_unread(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.read_at == None)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )


@notif_router.get("/unread/count", response_model=UnreadCountResponse)
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = get_unread_count(db, current_user.id)
    return UnreadCountResponse(count=count)


@notif_router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return mark_notification_read(db, notification_id, current_user.id)


@notif_router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    db.query(Notification).filter(
        Notification.user_id == current_user.id, Notification.read_at == None
    ).update({"read_at": now, "status": "READ"})
    db.commit()
    return {"status": "ok"}
