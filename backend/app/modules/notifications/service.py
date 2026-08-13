from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.factory import Factory
from app.models.notification import Notification
from app.models.user import User


def create_notification(
    db: Session,
    factory_id: int,
    notification_type: str,
    severity: str,
    title: str,
    message: str,
    user_id: int | None = None,
    deduplication_key: str | None = None,
    rule_id: str | None = None,
    cooldown_minutes: int | None = None,
    value: float | None = None,
    threshold: float | None = None,
    unit: str | None = None,
    source: str | None = None,
    alert_metadata: dict | None = None,
) -> Notification:
    """
    Two dedup strategies coexist: the original date-scoped
    deduplication_key (Step 14, still used by callers that haven't been
    migrated to rule_id) and the new cooldown-based check (23.18-23.19)
    — "don't recreate while a matching, still-active alert was created
    within the cooldown window". The cooldown check is the more correct
    one (an alert that resolves in 5 minutes shouldn't block a fresh one
    from firing 10 minutes later just because they're the same calendar
    day), so new rules should prefer rule_id + cooldown_minutes.
    """
    if deduplication_key:
        existing = db.scalar(
            select(Notification).where(
                Notification.deduplication_key == deduplication_key
            )
        )

        if existing:
            return existing

    if rule_id and cooldown_minutes is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)

        existing = db.scalar(
            select(Notification)
            .where(
                Notification.factory_id == factory_id,
                Notification.rule_id == rule_id,
                Notification.status.notin_(["RESOLVED", "DISMISSED"]),
                Notification.created_at >= cutoff,
            )
            .order_by(Notification.created_at.desc())
        )

        if existing:
            return existing

    notification = Notification(
        factory_id=factory_id,
        user_id=user_id,
        type=notification_type,
        severity=severity,
        title=title,
        message=message,
        is_read=False,
        status="UNREAD",
        deduplication_key=deduplication_key,
        rule_id=rule_id,
        value=value,
        threshold=threshold,
        unit=unit,
        source=source,
        alert_metadata=alert_metadata,
        created_at=datetime.now(timezone.utc),
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def get_notifications(
    db: Session,
    factory_id: int,
    status_filter: str | None = None,
    severity_filter: str | None = None,
    type_filter: str | None = None,
) -> list[Notification]:
    query = select(Notification).where(Notification.factory_id == factory_id)

    if status_filter:
        query = query.where(Notification.status == status_filter)
    if severity_filter:
        query = query.where(Notification.severity == severity_filter)
    if type_filter:
        query = query.where(Notification.type == type_filter)

    return db.scalars(query.order_by(Notification.created_at.desc())).all()


def get_unread_count(db: Session, factory_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.factory_id == factory_id,
            Notification.is_read.is_(False),
        )
    ) or 0


def mark_all_as_read(db: Session, factory_id: int) -> None:
    now = datetime.now(timezone.utc)

    db.execute(
        update(Notification)
        .where(
            Notification.factory_id == factory_id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True, status="READ", read_at=now)
    )
    db.commit()


def _get_owned_notification(
    db: Session,
    current_user: User,
    notification_id: int,
) -> Notification:
    """
    14.13's endpoint (PATCH /api/v1/notifications/{id}/read) has no
    factory_id in its path, unlike every other endpoint in this codebase
    — so get_accessible_factory can't gate it. Ownership is validated
    here instead, by joining through the notification's own factory to
    the current user's organization. 14.11 is explicit that this check
    must not be skipped just because the URL shape is different.
    """
    notification = db.scalar(
        select(Notification)
        .join(Factory, Factory.id == Notification.factory_id)
        .where(
            Notification.id == notification_id,
            Factory.organization_id == current_user.organization_id,
        )
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return notification


def mark_as_read(db: Session, current_user: User, notification_id: int) -> Notification:
    notification = _get_owned_notification(db, current_user, notification_id)

    notification.is_read = True
    notification.status = "READ"
    notification.read_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notification)

    return notification


def resolve_notification(
    db: Session, current_user: User, notification_id: int
) -> Notification:
    """23.20: READ -> RESOLVED (the underlying issue was addressed)."""
    notification = _get_owned_notification(db, current_user, notification_id)

    notification.status = "RESOLVED"
    notification.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notification)

    return notification


def dismiss_notification(
    db: Session, current_user: User, notification_id: int
) -> Notification:
    """23.20: UNREAD -> DISMISSED (the user doesn't care about this one)."""
    notification = _get_owned_notification(db, current_user, notification_id)

    notification.status = "DISMISSED"
    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification
