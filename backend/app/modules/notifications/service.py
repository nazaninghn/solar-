from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.factory import Factory
from app.models.notification import Notification
from app.models.user import User

# 30.29: severity describes how bad the underlying condition is;
# priority describes how urgently a human should be interrupted. They
# usually correlate, so this is the fallback whenever a caller doesn't
# pass an explicit priority — not every rule needs its own opinion.
_SEVERITY_PRIORITY_DEFAULTS = {
    "CRITICAL": "URGENT",
    "WARNING": "HIGH",
    "SUCCESS": "LOW",
    "INFO": "LOW",
}


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
    priority: str | None = None,
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
        priority=priority or _SEVERITY_PRIORITY_DEFAULTS.get(severity, "NORMAL"),
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

    # 30.14-30.15: dispatch lives here, not in each rule/caller — a
    # single funnel point means no call site can forget to fan out to
    # email/SMS, and the cooldown-deduplicated "return existing" paths
    # above never reach this line, so a suppressed duplicate correctly
    # never re-dispatches.
    from app.notifications.delivery import dispatch_notification_deliveries

    dispatch_notification_deliveries(db, notification)

    return notification


def get_notifications(
    db: Session,
    factory_id: int,
    status_filter: str | None = None,
    severity_filter: str | None = None,
    type_filter: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Notification], int]:
    """30.9: notifications accumulate indefinitely with no retention job
    (unlike device telemetry, Step 26) — pagination was a real gap, not
    just a nice-to-have, once a factory has months of alert history."""
    query = select(Notification).where(Notification.factory_id == factory_id)

    if status_filter:
        query = query.where(Notification.status == status_filter)
    if severity_filter:
        query = query.where(Notification.severity == severity_filter)
    if type_filter:
        query = query.where(Notification.type == type_filter)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    items = db.scalars(
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return items, total


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


def acknowledge_notification(
    db: Session, current_user: User, notification_id: int
) -> Notification:
    """
    30.24-30.25: "a human has seen this and is on it" — distinct from
    READ (may have just been glanced at in a list) and distinct from
    RESOLVED (the underlying issue may still be actively being worked,
    not fixed yet). Doesn't require the notification to be in any
    particular prior status — acknowledging an already-read alert, or
    one nobody's opened yet, are both legitimate.
    """
    notification = _get_owned_notification(db, current_user, notification_id)

    notification.status = "ACKNOWLEDGED"
    notification.acknowledged_by = current_user.id
    notification.acknowledged_at = datetime.now(timezone.utc)

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


def auto_resolve_notification(db: Session, notification: Notification) -> None:
    """
    28.29: the system-driven counterpart to resolve_notification — no
    current_user, since this runs from the alert-evaluation pipeline
    (a rule re-evaluated and no longer finds a violation), not a user
    clicking anything.
    """
    notification.status = "RESOLVED"
    notification.resolved_at = datetime.now(timezone.utc)

    db.commit()
