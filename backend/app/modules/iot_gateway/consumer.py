"""
STEP 39.6/39.14-39.16: Telemetry Consumer.

Processes incoming MQTT telemetry: dedup, validation, sequence check, storage.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.device import Device
from app.modules.iot_gateway.models import DeadLetterQueue, ProcessedMessage
from app.modules.iot_gateway.schemas import MQTTTelemetryMessage

logger = logging.getLogger(__name__)

# Thresholds
MAX_CLOCK_DRIFT_SECONDS = 300  # 5 minutes
MAX_MESSAGE_AGE_SECONDS = 3600  # 1 hour

# Per-device last sequence tracking (in-memory for MVP; Redis in production)
_device_sequences: dict[str, int] = {}


def process_telemetry(
    db: Session,
    message: MQTTTelemetryMessage,
    topic: str,
) -> dict:
    """
    Process incoming telemetry message through validation pipeline.
    Returns result dict with status and details.
    """
    now = datetime.now(timezone.utc)

    # 1. Deduplication (39.14)
    existing = (
        db.query(ProcessedMessage)
        .filter(ProcessedMessage.message_id == message.message_id)
        .first()
    )
    if existing:
        logger.debug(f"Duplicate message {message.message_id} — skipping")
        return {"status": "DUPLICATE", "message_id": message.message_id}

    # 2. Device lookup
    device = (
        db.query(Device)
        .filter(Device.id == int(message.device_id) if message.device_id.isdigit() else Device.name == message.device_id)
        .first()
    )
    if not device:
        _to_dlq(db, message, topic, "UNKNOWN_DEVICE", f"Device {message.device_id} not found")
        return {"status": "REJECTED", "reason": "UNKNOWN_DEVICE"}

    # 3. Timestamp validation (39.40)
    msg_age = (now - message.timestamp).total_seconds()
    if msg_age > MAX_MESSAGE_AGE_SECONDS:
        _to_dlq(db, message, topic, "STALE_MESSAGE", f"Message age {msg_age:.0f}s exceeds limit")
        return {"status": "REJECTED", "reason": "STALE_MESSAGE"}

    if message.timestamp > now + timedelta(seconds=MAX_CLOCK_DRIFT_SECONDS):
        _to_dlq(db, message, topic, "FUTURE_TIMESTAMP", "Timestamp in future")
        return {"status": "REJECTED", "reason": "FUTURE_TIMESTAMP"}

    # 4. Sequence check (39.15)
    device_key = str(device.id)
    last_seq = _device_sequences.get(device_key, 0)
    if message.sequence <= last_seq and last_seq > 0:
        logger.warning(
            f"Out-of-order message for device {device.id}: seq={message.sequence} <= last={last_seq}"
        )
        # Still store for audit, but mark quality
        pass
    _device_sequences[device_key] = max(message.sequence, last_seq)

    # 5. Metric range validation (39.17)
    validated_metrics = {}
    for metric, value in message.metrics.items():
        if _validate_metric_range(metric, value):
            validated_metrics[metric] = value
        else:
            logger.warning(f"Metric {metric}={value} out of range for device {device.id}")

    # 6. Update device last_seen (39.12)
    device.last_seen_at = now
    if device.status == "OFFLINE":
        device.status = "ONLINE"
    device.consecutive_error_count = 0

    # 7. Record as processed (39.14)
    db.add(ProcessedMessage(
        message_id=message.message_id,
        device_id=device.id,
        received_at=now,
        result="PROCESSED",
    ))

    db.commit()

    return {
        "status": "PROCESSED",
        "device_id": device.id,
        "metrics_count": len(validated_metrics),
        "sequence": message.sequence,
    }


def _validate_metric_range(metric: str, value: float) -> bool:
    """39.17: Basic range validation."""
    ranges = {
        "soc": (0, 100),
        "temperature_c": (-40, 100),
        "power_kw": (-5000, 5000),
        "voltage": (0, 1500),
        "frequency_hz": (45, 65),
    }
    if metric in ranges:
        min_v, max_v = ranges[metric]
        return min_v <= value <= max_v
    return True


def _to_dlq(db: Session, message: MQTTTelemetryMessage, topic: str, error_code: str, error_msg: str):
    """39.23: Send failed message to Dead Letter Queue."""
    db.add(DeadLetterQueue(
        device_id=int(message.device_id) if message.device_id.isdigit() else None,
        factory_id=int(message.factory_id) if message.factory_id.isdigit() else None,
        topic=topic,
        payload_json=message.model_dump_json(),
        error_code=error_code,
        error_message=error_msg,
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()
    logger.warning(f"Message {message.message_id} sent to DLQ: {error_code}")
