import uuid
from datetime import datetime, time, timedelta, timezone

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.jobs.escalation_jobs import (
    ESCALATION_THRESHOLD_MINUTES,
    escalate_unacknowledged_critical_alerts,
)
from app.main import app
from app.models.factory import Factory
from app.models.notification import Notification
from app.models.notification_delivery import NotificationDelivery
from app.models.user import User
from app.modules.notifications.preferences_service import get_or_create_preferences
from app.modules.notifications.service import (
    acknowledge_notification,
    create_notification,
    dismiss_notification,
    resolve_notification,
)
from app.notifications.delivery import is_within_quiet_hours

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@pytest.solarflow.com"


def _register_user_and_factory():
    """Returns (access_token, User, Factory) for a fresh COMPANY_ADMIN
    in a fresh org+factory, isolated from any other test's data."""
    email = _unique_email("notif-delivery")

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123!",
            "full_name": "Notification Delivery Admin",
            "organization_name": f"Notif Delivery Org {uuid.uuid4().hex[:6]}",
        },
    )

    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "TestPass123!"}
    )
    token = login.json()["access_token"]

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        factory = Factory(
            organization_id=user.organization_id,
            name="Notif Delivery Test Factory",
        )
        db.add(factory)
        db.commit()
        db.refresh(factory)
        db.refresh(user)

        return token, user.id, factory.id
    finally:
        db.close()


# --- Quiet hours (30.20) ---


def test_quiet_hours_same_day_window():
    class FakePrefs:
        quiet_hours_start = time(22, 0)
        quiet_hours_end = time(23, 0)

    assert is_within_quiet_hours(FakePrefs(), datetime(2026, 1, 1, 22, 30, tzinfo=timezone.utc)) is True
    assert is_within_quiet_hours(FakePrefs(), datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)) is False


def test_quiet_hours_overnight_wraparound():
    class FakePrefs:
        quiet_hours_start = time(23, 0)
        quiet_hours_end = time(7, 0)

    # 23:30 and 03:00 both fall inside a 23:00->07:00 overnight window.
    assert is_within_quiet_hours(FakePrefs(), datetime(2026, 1, 1, 23, 30, tzinfo=timezone.utc)) is True
    assert is_within_quiet_hours(FakePrefs(), datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc)) is True
    assert is_within_quiet_hours(FakePrefs(), datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)) is False


def test_quiet_hours_disabled_when_unset():
    class FakePrefs:
        quiet_hours_start = None
        quiet_hours_end = None

    assert is_within_quiet_hours(FakePrefs()) is False


# --- Priority defaults (30.29) ---


def test_create_notification_defaults_priority_from_severity():
    _, _, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="CRITICAL",
            title="Test critical",
            message="test",
        )
        assert notification.priority == "URGENT"
    finally:
        db.close()


def test_create_notification_explicit_priority_overrides_default():
    _, _, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="INFO",
            title="Test info",
            message="test",
            priority="HIGH",
        )
        assert notification.priority == "HIGH"
    finally:
        db.close()


# --- Delivery tracking (30.26) ---


def test_dispatch_records_in_app_delivery():
    _, _, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="WARNING",
            title="Delivery tracking test",
            message="test",
        )

        deliveries = (
            db.query(NotificationDelivery)
            .filter(NotificationDelivery.notification_id == notification.id)
            .all()
        )
        channels = {d.channel for d in deliveries}
        assert "IN_APP" in channels
        assert all(d.status == "DELIVERED" for d in deliveries if d.channel == "IN_APP")
    finally:
        db.close()


def test_dispatch_sends_email_when_enabled_and_not_quiet():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        preferences = get_or_create_preferences(db, user_id)
        preferences.email_enabled = True
        preferences.quiet_hours_start = None
        preferences.quiet_hours_end = None
        db.commit()

        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="WARNING",
            title="Email delivery test",
            message="test",
        )

        deliveries = (
            db.query(NotificationDelivery)
            .filter(
                NotificationDelivery.notification_id == notification.id,
                NotificationDelivery.channel == "EMAIL",
            )
            .all()
        )
        assert len(deliveries) == 1
        assert deliveries[0].user_id == user_id
        assert deliveries[0].status == "DELIVERED"
    finally:
        db.close()


def test_dispatch_suppresses_non_urgent_email_during_quiet_hours():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        preferences = get_or_create_preferences(db, user_id)
        preferences.email_enabled = True
        # A window that covers "now" regardless of time of day: an
        # almost-24h span with only a 1-minute gap.
        now = datetime.now(timezone.utc).time()
        preferences.quiet_hours_start = time(0, 0)
        preferences.quiet_hours_end = time(23, 59)
        db.commit()

        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="WARNING",  # non-CRITICAL, non-URGENT -> suppressible
            title="Quiet hours suppression test",
            message="test",
        )

        deliveries = (
            db.query(NotificationDelivery)
            .filter(
                NotificationDelivery.notification_id == notification.id,
                NotificationDelivery.channel == "EMAIL",
            )
            .all()
        )
        assert len(deliveries) == 0
    finally:
        db.close()


def test_dispatch_critical_breaks_through_quiet_hours():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        preferences = get_or_create_preferences(db, user_id)
        preferences.email_enabled = True
        preferences.quiet_hours_start = time(0, 0)
        preferences.quiet_hours_end = time(23, 59)
        db.commit()

        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="CRITICAL",
            title="Critical breaks quiet hours",
            message="test",
        )

        deliveries = (
            db.query(NotificationDelivery)
            .filter(
                NotificationDelivery.notification_id == notification.id,
                NotificationDelivery.channel == "EMAIL",
            )
            .all()
        )
        assert len(deliveries) == 1
    finally:
        db.close()


# --- Acknowledgement / resolve / dismiss (30.24-30.25, 23.20) ---


def test_acknowledge_notification_sets_fields():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="WARNING",
            title="Ack test",
            message="test",
        )
        user = db.get(User, user_id)

        acknowledged = acknowledge_notification(db, user, notification.id)

        assert acknowledged.status == "ACKNOWLEDGED"
        assert acknowledged.acknowledged_by == user_id
        assert acknowledged.acknowledged_at is not None
    finally:
        db.close()


def test_resolve_notification_sets_resolved_at():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="WARNING",
            title="Resolve test",
            message="test",
        )
        user = db.get(User, user_id)

        resolved = resolve_notification(db, user, notification.id)

        assert resolved.status == "RESOLVED"
        assert resolved.resolved_at is not None
    finally:
        db.close()


def test_dismiss_notification_sets_status():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="WARNING",
            title="Dismiss test",
            message="test",
        )
        user = db.get(User, user_id)

        dismissed = dismiss_notification(db, user, notification.id)

        assert dismissed.status == "DISMISSED"
        assert dismissed.is_read is True
    finally:
        db.close()


# --- Cooldown dedup (23.18-23.19) — the mechanism generate_daily_summary
# (app/jobs/daily_summary_jobs.py) relies on for "once per day" ---


def test_cooldown_dedup_returns_existing_within_window():
    _, _, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        first = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="INFO",
            title="Daily Energy Summary",
            message="first run",
            rule_id="DAILY_SUMMARY",
            cooldown_minutes=1200,
        )

        second = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="INFO",
            title="Daily Energy Summary",
            message="second run, same window",
            rule_id="DAILY_SUMMARY",
            cooldown_minutes=1200,
        )

        assert second.id == first.id

        count = (
            db.query(Notification)
            .filter(
                Notification.factory_id == factory_id,
                Notification.rule_id == "DAILY_SUMMARY",
            )
            .count()
        )
        assert count == 1
    finally:
        db.close()


def test_cooldown_dedup_allows_new_after_window_expires():
    _, _, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        first = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="INFO",
            title="Daily Energy Summary",
            message="first run",
            rule_id="DAILY_SUMMARY",
            cooldown_minutes=1200,
        )
        # Simulate the cooldown window having already elapsed.
        first.created_at = datetime.now(timezone.utc) - timedelta(hours=21)
        db.commit()

        second = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="ENERGY",
            severity="INFO",
            title="Daily Energy Summary",
            message="next day",
            rule_id="DAILY_SUMMARY",
            cooldown_minutes=1200,
        )

        assert second.id != first.id
    finally:
        db.close()


# --- Escalation (30.13) ---


def test_escalation_escalates_unacknowledged_critical_and_notifies_fallback_admin():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="BATTERY",
            severity="CRITICAL",
            title="Battery critical",
            message="test",
        )
        # Push it past the escalation threshold without touching
        # acknowledged_at/escalated_at.
        notification.created_at = datetime.now(timezone.utc) - timedelta(
            minutes=ESCALATION_THRESHOLD_MINUTES + 5
        )
        db.commit()

        escalate_unacknowledged_critical_alerts()

        db.refresh(notification)
        assert notification.escalated_at is not None

        # No FACTORY_MANAGER/ENERGY_MANAGER exists for this fresh org, so
        # the fallback path should have notified the COMPANY_ADMIN
        # (the registering user) instead.
        escalation_notice = (
            db.query(Notification)
            .filter(
                Notification.factory_id == factory_id,
                Notification.source == "ESCALATION",
                Notification.user_id == user_id,
            )
            .first()
        )
        assert escalation_notice is not None
        assert escalation_notice.title.startswith("ESCALATED:")
    finally:
        db.close()


def test_escalation_does_not_reescalate_same_notification():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="BATTERY",
            severity="CRITICAL",
            title="Battery critical (no re-escalate)",
            message="test",
        )
        notification.created_at = datetime.now(timezone.utc) - timedelta(
            minutes=ESCALATION_THRESHOLD_MINUTES + 5
        )
        db.commit()

        escalate_unacknowledged_critical_alerts()
        db.refresh(notification)
        first_escalated_at = notification.escalated_at
        assert first_escalated_at is not None

        escalate_unacknowledged_critical_alerts()
        db.refresh(notification)
        assert notification.escalated_at == first_escalated_at

        escalation_count = (
            db.query(Notification)
            .filter(
                Notification.factory_id == factory_id,
                Notification.source == "ESCALATION",
                Notification.alert_metadata["escalated_notification_id"].as_integer()
                == notification.id,
            )
            .count()
        )
        assert escalation_count == 1
    finally:
        db.close()


def test_escalation_skips_already_acknowledged_notification():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="BATTERY",
            severity="CRITICAL",
            title="Battery critical (already ack'd)",
            message="test",
        )
        notification.created_at = datetime.now(timezone.utc) - timedelta(
            minutes=ESCALATION_THRESHOLD_MINUTES + 5
        )
        notification.acknowledged_at = datetime.now(timezone.utc)
        notification.acknowledged_by = user_id
        db.commit()

        escalate_unacknowledged_critical_alerts()

        db.refresh(notification)
        assert notification.escalated_at is None
    finally:
        db.close()


# --- DEVICE notification type / preference (30.10) ---


def test_dispatch_respects_device_alerts_preference_flag():
    token, user_id, factory_id = _register_user_and_factory()

    db = SessionLocal()
    try:
        preferences = get_or_create_preferences(db, user_id)
        preferences.email_enabled = True
        preferences.device_alerts = False
        preferences.quiet_hours_start = None
        preferences.quiet_hours_end = None
        db.commit()

        notification = create_notification(
            db=db,
            factory_id=factory_id,
            notification_type="DEVICE",
            severity="WARNING",
            title="Device offline",
            message="test",
        )

        deliveries = (
            db.query(NotificationDelivery)
            .filter(
                NotificationDelivery.notification_id == notification.id,
                NotificationDelivery.channel == "EMAIL",
            )
            .all()
        )
        assert len(deliveries) == 0
    finally:
        db.close()
