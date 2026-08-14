"""
STEP 33.8: Telemetry Ingestion & Normalization Service.

Validates incoming telemetry, assigns quality flags, stores normalized data.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.device import Device
from app.modules.gateway.models import QUALITY_GOOD, QUALITY_INVALID, QUALITY_OUT_OF_RANGE, DeviceTelemetry
from app.modules.gateway.schemas import TelemetryPayload

logger = logging.getLogger(__name__)

# Acceptable ranges for validation
METRIC_RANGES = {
    "soc": (0, 100),
    "power_kw": (-2000, 2000),
    "voltage": (0, 1500),
    "temperature_c": (-40, 80),
    "energy_kwh": (0, 100000),
    "frequency_hz": (45, 65),
    "current_a": (-5000, 5000),
}

# Max age for telemetry timestamp (reject data older than this)
MAX_TELEMETRY_AGE = timedelta(hours=1)


def validate_telemetry(payload: TelemetryPayload) -> tuple[bool, str | None]:
    """33.8: Validate incoming telemetry payload."""
    now = datetime.now(timezone.utc)

    # Timestamp validation
    if payload.timestamp > now + timedelta(minutes=5):
        return False, "Timestamp is in the future"
    if payload.timestamp < now - MAX_TELEMETRY_AGE:
        return False, "Timestamp too old"

    return True, None


def get_quality_flag(metric: str, value: float) -> str:
    """33.9: Assign quality flag based on value range."""
    if metric in METRIC_RANGES:
        min_val, max_val = METRIC_RANGES[metric]
        if value < min_val or value > max_val:
            return QUALITY_OUT_OF_RANGE
    return QUALITY_GOOD


def ingest_telemetry(
    db: Session,
    device: Device,
    payload: TelemetryPayload,
) -> list[DeviceTelemetry]:
    """
    33.8: Process and store telemetry data.
    Extracts individual metrics from payload, validates, and stores.
    """
    # Validate
    valid, error = validate_telemetry(payload)
    if not valid:
        logger.warning(
            f"Telemetry rejected for device {device.id}: {error}",
            extra={"device_id": device.id, "reason": error},
        )
        return []

    records: list[DeviceTelemetry] = []
    metrics_to_store = {
        "soc": (payload.soc, "%"),
        "power_kw": (payload.power_kw, "kW"),
        "voltage": (payload.voltage, "V"),
        "temperature_c": (payload.temperature_c, "°C"),
        "energy_kwh": (payload.energy_kwh, "kWh"),
        "frequency_hz": (payload.frequency_hz, "Hz"),
        "current_a": (payload.current_a, "A"),
    }

    for metric, (value, unit) in metrics_to_store.items():
        if value is None:
            continue

        quality = get_quality_flag(metric, value)
        if quality == QUALITY_OUT_OF_RANGE:
            logger.warning(
                f"Metric {metric}={value} out of range for device {device.id}",
                extra={"device_id": device.id, "metric": metric, "value": value},
            )

        record = DeviceTelemetry(
            device_id=device.id,
            timestamp=payload.timestamp,
            metric=metric,
            value=value,
            unit=unit,
            quality=quality,
            source="telemetry",
        )
        db.add(record)
        records.append(record)

    # Update device last_seen
    device.last_seen_at = payload.timestamp
    device.status = "ONLINE"
    device.consecutive_error_count = 0

    db.commit()
    return records
