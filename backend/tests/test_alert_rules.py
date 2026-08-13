from datetime import datetime, timedelta, timezone

from app.notifications.rules import (
    BatteryLowRule,
    BatteryRuleContext,
    PriceRuleContext,
    PriceSpikeRule,
    WeatherForecastRule,
    WeatherRuleContext,
)


def test_soc_15_percent_is_warning():
    """Test 1 (23.36): SOC=15% -> WARNING."""
    rule = BatteryLowRule()
    result = rule.evaluate(BatteryRuleContext(soc_percent=15))

    assert result is not None
    assert result["severity"] == "WARNING"


def test_soc_8_percent_is_critical():
    """Test 2 (23.36): SOC=8% -> CRITICAL."""
    rule = BatteryLowRule()
    result = rule.evaluate(BatteryRuleContext(soc_percent=8))

    assert result is not None
    assert result["severity"] == "CRITICAL"


def test_price_spike_current_13000_average_10000_is_warning():
    """Test 3 (23.36): current=13000, average=10000 (exactly +30%) -> WARNING."""
    rule = PriceSpikeRule()
    result = rule.evaluate(
        PriceRuleContext(
            current_price=13000, average_price_24h=10000, price_level=""
        )
    )

    assert result is not None
    assert result["severity"] == "WARNING"


def test_solar_decrease_35_percent_is_warning():
    """Test 4 (23.36): forecast solar decrease=35% -> WARNING."""
    rule = WeatherForecastRule()
    result = rule.evaluate(WeatherRuleContext(solar_reduction_percent=35))

    assert result is not None
    assert result["severity"] == "WARNING"


def test_duplicate_alert_within_cooldown_is_not_recreated():
    """Test 5 (23.36): same rule, same factory, within cooldown -> no duplicate."""
    from sqlalchemy import delete, select

    from app.database.session import SessionLocal
    from app.models.notification import Notification
    from app.modules.notifications.service import create_notification

    db = SessionLocal()

    # This test hits the real dev DB with no fixture teardown — without
    # this, rows from earlier pytest runs (once outside the 60-minute
    # cooldown window) accumulate and inflate the count below on any run
    # more than an hour after a previous one.
    db.execute(delete(Notification).where(Notification.rule_id == "TEST_COOLDOWN_RULE"))
    db.commit()

    first = create_notification(
        db=db,
        factory_id=1,
        notification_type="BATTERY",
        severity="WARNING",
        title="Battery level is low",
        message="test",
        rule_id="TEST_COOLDOWN_RULE",
        cooldown_minutes=60,
    )
    second = create_notification(
        db=db,
        factory_id=1,
        notification_type="BATTERY",
        severity="WARNING",
        title="Battery level is low",
        message="test",
        rule_id="TEST_COOLDOWN_RULE",
        cooldown_minutes=60,
    )

    assert first.id == second.id

    count = len(
        db.scalars(
            select(Notification).where(
                Notification.rule_id == "TEST_COOLDOWN_RULE"
            )
        ).all()
    )
    assert count == 1


def test_mark_as_read_transitions_unread_to_read():
    """Test 6 (23.36): UNREAD -> READ."""
    from app.database.session import SessionLocal
    from app.models.user import User
    from app.modules.notifications.service import create_notification, mark_as_read
    from sqlalchemy import select

    db = SessionLocal()
    user = db.scalar(select(User).limit(1))

    notification = create_notification(
        db=db,
        factory_id=1,
        notification_type="SYSTEM",
        severity="INFO",
        title="test read transition",
        message="test",
    )
    assert notification.status == "UNREAD"

    updated = mark_as_read(db, current_user=user, notification_id=notification.id)

    assert updated.status == "READ"


def test_resolve_transitions_read_to_resolved():
    """Test 7 (23.36): READ -> RESOLVED."""
    from app.database.session import SessionLocal
    from app.models.user import User
    from app.modules.notifications.service import (
        create_notification,
        mark_as_read,
        resolve_notification,
    )
    from sqlalchemy import select

    db = SessionLocal()
    user = db.scalar(select(User).limit(1))

    notification = create_notification(
        db=db,
        factory_id=1,
        notification_type="SYSTEM",
        severity="INFO",
        title="test resolve transition",
        message="test",
    )
    mark_as_read(db, current_user=user, notification_id=notification.id)

    resolved = resolve_notification(
        db, current_user=user, notification_id=notification.id
    )

    assert resolved.status == "RESOLVED"
    assert resolved.resolved_at is not None
