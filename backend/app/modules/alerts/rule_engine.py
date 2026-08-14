"""
STEP 40.9-40.17: Alert Rule Engine.

Evaluates conditions, manages cooldown, deduplication, and alert creation.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.alerts.models import (
    ALERT_OPEN,
    SEV_HIGH,
    SEV_MEDIUM,
    Alert,
    AlertSuppression,
)

logger = logging.getLogger(__name__)


def evaluate_battery_low(
    db: Session, factory_id: int, battery_soc: float, threshold: float = 20.0
) -> Alert | None:
    """40.10: Low battery SOC alert."""
    if battery_soc >= threshold:
        return None
    return _create_alert_if_new(
        db=db,
        factory_id=factory_id,
        alert_type="BATTERY_LOW_SOC",
        severity=SEV_HIGH if battery_soc < 15 else SEV_MEDIUM,
        title=f"Battery SOC critical: {battery_soc:.1f}%",
        description=f"Battery state of charge dropped to {battery_soc:.1f}%, below threshold of {threshold}%.",
        source_type="battery",
    )


def evaluate_device_offline(
    db: Session, factory_id: int, device_id: int, device_name: str, last_seen: datetime | None
) -> Alert | None:
    """40.12: Device offline alert."""
    if last_seen is None:
        return None
    now = datetime.now(timezone.utc)
    age = (now - last_seen).total_seconds()
    if age < 300:  # 5 min threshold
        return None
    return _create_alert_if_new(
        db=db,
        factory_id=factory_id,
        alert_type="DEVICE_OFFLINE",
        severity=SEV_HIGH,
        title=f"Device offline: {device_name}",
        description=f"Device {device_name} (ID:{device_id}) last seen {age/60:.0f} minutes ago.",
        source_type="device",
        source_id=device_id,
    )


def evaluate_high_grid_price(
    db: Session, factory_id: int, current_price: float, threshold: float = 0.30
) -> Alert | None:
    """40.11: High grid price alert."""
    if current_price < threshold:
        return None
    return _create_alert_if_new(
        db=db,
        factory_id=factory_id,
        alert_type="HIGH_GRID_PRICE",
        severity=SEV_MEDIUM,
        title=f"High grid price: €{current_price:.3f}/kWh",
        description=f"Grid electricity price at €{current_price:.3f}/kWh exceeds threshold of €{threshold:.3f}/kWh.",
        source_type="pricing",
    )


def evaluate_forecast_deviation(
    db: Session, factory_id: int, forecast_kwh: float, actual_kwh: float, threshold_pct: float = 30.0
) -> Alert | None:
    """40.13: Forecast deviation alert."""
    if forecast_kwh <= 0:
        return None
    deviation_pct = ((forecast_kwh - actual_kwh) / forecast_kwh) * 100
    if deviation_pct < threshold_pct:
        return None
    return _create_alert_if_new(
        db=db,
        factory_id=factory_id,
        alert_type="FORECAST_DEVIATION",
        severity=SEV_MEDIUM,
        title=f"Solar forecast deviation: {deviation_pct:.0f}% below expected",
        description=f"Actual solar production ({actual_kwh:.0f} kWh) is {deviation_pct:.0f}% below forecast ({forecast_kwh:.0f} kWh).",
        source_type="forecast",
    )


def _create_alert_if_new(
    db: Session,
    factory_id: int,
    alert_type: str,
    severity: str,
    title: str,
    description: str,
    source_type: str | None = None,
    source_id: int | None = None,
) -> Alert | None:
    """Create alert with deduplication and cooldown."""
    now = datetime.now(timezone.utc)

    # Dedup key (40.17). 85: usedforsecurity=False - this is a dedup
    # fingerprint, not a security use of MD5.
    dedup_key = hashlib.md5(
        f"{factory_id}:{alert_type}:{source_id or ''}".encode(), usedforsecurity=False
    ).hexdigest()

    # Check suppression (40.18)
    suppressed = (
        db.query(AlertSuppression)
        .filter(
            AlertSuppression.factory_id == factory_id,
            (AlertSuppression.alert_type == alert_type) | (AlertSuppression.alert_type == None),
            AlertSuppression.starts_at <= now,
            AlertSuppression.ends_at >= now,
        )
        .first()
    )
    if suppressed:
        logger.debug(f"Alert {alert_type} suppressed for factory {factory_id}")
        return None

    # Check existing open alert (dedup)
    existing = (
        db.query(Alert)
        .filter(
            Alert.dedup_key == dedup_key,
            Alert.status == ALERT_OPEN,
        )
        .first()
    )
    if existing:
        # Update last_seen (40.16 cooldown — don't create new)
        existing.last_seen_at = now
        db.commit()
        return None

    # Check cooldown (last resolved alert of same type)
    last_resolved = (
        db.query(Alert)
        .filter(
            Alert.dedup_key == dedup_key,
            Alert.resolved_at != None,
        )
        .order_by(Alert.resolved_at.desc())
        .first()
    )
    if last_resolved and last_resolved.resolved_at:
        cooldown = timedelta(minutes=30)
        if (now - last_resolved.resolved_at) < cooldown:
            return None

    # Create new alert
    alert = Alert(
        factory_id=factory_id,
        type=alert_type,
        severity=severity,
        title=title,
        description=description,
        status=ALERT_OPEN,
        source_type=source_type,
        source_id=source_id,
        dedup_key=dedup_key,
        started_at=now,
        last_seen_at=now,
        created_at=now,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    logger.info(f"Alert created: {alert_type} severity={severity} factory={factory_id}")
    return alert
