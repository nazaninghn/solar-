import asyncio
import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.auth.access_control import list_users_with_factory_access
from app.models.factory import Factory
from app.models.notification import Notification
from app.models.notification_delivery import NotificationDelivery
from app.models.notification_preference import NotificationPreference
from app.modules.notifications.preferences_service import get_or_create_preferences
from app.notifications.channels.email import send_notification_email
from app.notifications.channels.in_app import send_in_app
from app.notifications.channels.sms import send_notification_sms

# 30.5's types mapped onto the closest NotificationPreference category —
# RECOMMENDATION/FORECAST don't have a dedicated flag of their own
# (adding one per type felt like schema churn for a distinction users
# are unlikely to want split further); everything else maps 1:1.
_TYPE_TO_PREFERENCE_FIELD = {
    "BATTERY": "battery_alerts",
    "PRICE": "price_alerts",
    "WEATHER": "weather_alerts",
    "ENERGY": "energy_alerts",
    "FINANCIAL": "financial_alerts",
    "SYSTEM": "system_alerts",
    "DEVICE": "device_alerts",
    "RECOMMENDATION": "energy_alerts",
    "FORECAST": "weather_alerts",
}

_RETRY_BACKOFF_SECONDS = (1, 2)  # 30.27: 3 attempts total, waits between them


def is_within_quiet_hours(
    preferences: NotificationPreference, now: datetime | None = None
) -> bool:
    """30.20: handles the overnight-wraparound case (e.g. 23:00 -> 07:00)
    as well as a same-day window."""
    if preferences.quiet_hours_start is None or preferences.quiet_hours_end is None:
        return False

    current_time = (now or datetime.now(timezone.utc)).time()
    start, end = preferences.quiet_hours_start, preferences.quiet_hours_end

    if start <= end:
        return start <= current_time < end

    return current_time >= start or current_time < end


def _send_with_retry(send_fn, *args) -> tuple[bool, str | None]:
    """
    30.27: 3 attempts, sync (dispatch runs inline, not on a queue — see
    module docstring below). The stub channels never actually fail, so
    this never sleeps in practice; the backoff only engages once a real
    provider that can genuinely fail replaces the stub.
    """
    last_error: str | None = None

    for attempt in range(3):
        try:
            if send_fn(*args):
                return True, None
            last_error = "Channel returned failure"
        except Exception as error:
            last_error = str(error)

        if attempt < 2:
            time.sleep(_RETRY_BACKOFF_SECONDS[attempt])

    return False, last_error


def _record_delivery(
    db: Session,
    notification: Notification,
    channel: str,
    success: bool,
    error_message: str | None,
    user_id: int | None = None,
) -> None:
    now = datetime.now(timezone.utc)

    db.add(
        NotificationDelivery(
            notification_id=notification.id,
            user_id=user_id,
            channel=channel,
            status="DELIVERED" if success else "FAILED",
            attempt_count=1,
            sent_at=now,
            delivered_at=now if success else None,
            failed_at=None if success else now,
            error_message=error_message,
            created_at=now,
        )
    )


def dispatch_notification_deliveries(db: Session, notification: Notification) -> None:
    """
    30.14-30.15's architecture: called after create_notification commits
    a new row, not from inside business logic — this is the one place
    that decides which channels a given alert goes out on. Runs inline
    (no Celery/queue exists in this project — Step 25's decision), which
    is safe here specifically because every channel is a fast stub; a
    real SMTP/SMS provider should move this to a background job before
    it's on the hot path of an API request.
    """
    factory = db.get(Factory, notification.factory_id)

    if factory is None:
        return

    send_in_app(notification)
    _record_delivery(db, notification, "IN_APP", True, None)

    preference_field = _TYPE_TO_PREFERENCE_FIELD.get(notification.type, "energy_alerts")
    is_urgent = notification.severity in ("CRITICAL",) or notification.priority == "URGENT"
    websocket_target_user_ids: list[int] = []

    for user in list_users_with_factory_access(db, factory):
        preferences = get_or_create_preferences(db, user.id)

        category_enabled = getattr(preferences, preference_field, True)
        quiet = is_within_quiet_hours(preferences)

        # 30.11-30.12: real-time push respects dashboard_enabled the
        # same way email respects email_enabled — 23.31 introduced this
        # flag before the WebSocket that would actually consume it
        # existed; this is that wiring.
        if preferences.dashboard_enabled and category_enabled:
            websocket_target_user_ids.append(user.id)

        # 30.20: CRITICAL/URGENT breaks through quiet hours; everything
        # else is suppressed during the window.
        if preferences.email_enabled and category_enabled and (is_urgent or not quiet):
            success, error = _send_with_retry(send_notification_email, user.email, notification)
            _record_delivery(db, notification, "EMAIL", success, error, user_id=user.id)

        # 30.18: SMS is CRITICAL-only, full stop — not subject to the
        # per-category flags the way email is, since it's an even more
        # interruptive channel reserved for the worst severity.
        if preferences.sms_enabled and notification.severity == "CRITICAL":
            # No phone number field exists on User yet — stubbed with a
            # placeholder so the dispatch path is exercised/testable;
            # wiring a real phone number is a User-model change outside
            # this step's scope.
            success, error = _send_with_retry(
                send_notification_sms, f"user-{user.id}", notification
            )
            _record_delivery(db, notification, "SMS", success, error, user_id=user.id)

    db.commit()

    _try_broadcast_over_websocket(notification, websocket_target_user_ids)


def _try_broadcast_over_websocket(notification: Notification, user_ids: list[int]) -> None:
    """
    create_notification (and therefore this function) is a plain sync
    call, but every real call site in this codebase (alert_jobs.py,
    recommendations/service.py) runs inside an async job that's already
    on a running event loop by the time it gets here — so the push can
    be scheduled with create_task() rather than blocking on it. Direct
    sync callers (pytest, a one-off script) have no running loop; the
    notification is still safely persisted either way, it just won't
    get pushed in real time — a degraded-but-correct fallback, not a
    failure.
    """
    if not user_ids:
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    from app.notifications.ws_manager import broadcast_notification_to_users

    loop.create_task(broadcast_notification_to_users(notification, user_ids))
