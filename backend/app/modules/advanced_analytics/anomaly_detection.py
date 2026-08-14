"""
STEP 45.27-45.31: Anomaly Detection.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.advanced_analytics.models import Anomaly

logger = logging.getLogger(__name__)


def detect_solar_anomaly(
    db: Session,
    factory_id: int,
    actual_kwh: float,
    expected_kwh: float,
    threshold_pct: float = 30.0,
) -> Anomaly | None:
    """Detect if solar production deviates significantly from expected."""
    if expected_kwh <= 0:
        return None
    deviation_pct = ((expected_kwh - actual_kwh) / expected_kwh) * 100
    if deviation_pct < threshold_pct:
        return None

    return _create_anomaly(
        db, factory_id, "SOLAR_PRODUCTION_DROP", "HIGH",
        actual_kwh, expected_kwh, deviation_pct,
    )


def detect_consumption_spike(
    db: Session,
    factory_id: int,
    current_kwh: float,
    baseline_kwh: float,
    threshold_pct: float = 50.0,
) -> Anomaly | None:
    """Detect unusual consumption increase."""
    if baseline_kwh <= 0:
        return None
    spike_pct = ((current_kwh - baseline_kwh) / baseline_kwh) * 100
    if spike_pct < threshold_pct:
        return None

    return _create_anomaly(
        db, factory_id, "CONSUMPTION_SPIKE", "MEDIUM",
        current_kwh, baseline_kwh, spike_pct,
    )


def detect_battery_anomaly(
    db: Session,
    factory_id: int,
    device_id: int,
    soc: float,
    expected_soc: float,
    threshold: float = 20.0,
) -> Anomaly | None:
    """Detect unexpected battery SOC behavior."""
    deviation = abs(soc - expected_soc)
    if deviation < threshold:
        return None

    anomaly = _create_anomaly(
        db, factory_id, "BATTERY_SOC_ANOMALY", "MEDIUM",
        soc, expected_soc, deviation,
    )
    if anomaly:
        anomaly.device_id = device_id
        db.commit()
    return anomaly


def _create_anomaly(
    db: Session,
    factory_id: int,
    anomaly_type: str,
    severity: str,
    observed: float,
    expected: float,
    deviation: float,
) -> Anomaly:
    now = datetime.now(timezone.utc)
    anomaly = Anomaly(
        factory_id=factory_id,
        type=anomaly_type,
        severity=severity,
        detected_at=now,
        observed_value=round(observed, 2),
        expected_value=round(expected, 2),
        deviation=round(deviation, 2),
        confidence=0.8,
        status="DETECTED",
    )
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    logger.info(f"Anomaly detected: {anomaly_type} factory={factory_id} deviation={deviation:.1f}")
    return anomaly
