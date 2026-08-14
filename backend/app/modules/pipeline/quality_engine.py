"""
STEP 34.9-34.13: Data Quality Engine.

Assigns quality flags, detects duplicates, late data, missing intervals,
and computes per-factory data quality scores.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.modules.gateway.models import QUALITY_GOOD, DeviceTelemetry
from app.modules.pipeline.models import DataQualityLog, MetricCatalog

logger = logging.getLogger(__name__)

# Quality constants
QUALITY_DUPLICATE = "DUPLICATE"
QUALITY_LATE = "LATE"
QUALITY_MISSING = "MISSING"
QUALITY_OUT_OF_RANGE = "OUT_OF_RANGE"
QUALITY_INVALID = "INVALID"

LATE_THRESHOLD = timedelta(minutes=5)


def compute_fingerprint(device_id: int, timestamp: datetime, metric: str) -> str:
    """34.11: Generate fingerprint for duplicate detection."""
    raw = f"{device_id}:{timestamp.isoformat()}:{metric}"
    return hashlib.md5(raw.encode()).hexdigest()


def is_duplicate(db: Session, device_id: int, timestamp: datetime, metric: str) -> bool:
    """34.11: Check if this exact data point already exists."""
    exists = (
        db.query(DeviceTelemetry)
        .filter(
            DeviceTelemetry.device_id == device_id,
            DeviceTelemetry.timestamp == timestamp,
            DeviceTelemetry.metric == metric,
        )
        .first()
    )
    return exists is not None


def is_late(device_timestamp: datetime, received_at: datetime) -> bool:
    """34.12: Check if data arrived significantly after event time."""
    return (received_at - device_timestamp) > LATE_THRESHOLD


def validate_range(metric_key: str, value: float, catalog: dict[str, MetricCatalog]) -> str:
    """34.10: Validate value against metric catalog ranges."""
    if metric_key not in catalog:
        return QUALITY_GOOD  # No catalog entry = trust it

    entry = catalog[metric_key]
    if entry.min_value is not None and value < entry.min_value:
        return QUALITY_OUT_OF_RANGE
    if entry.max_value is not None and value > entry.max_value:
        return QUALITY_OUT_OF_RANGE
    return QUALITY_GOOD


def compute_data_quality_score(
    db: Session,
    factory_id: int,
    date_str: str,
) -> DataQualityLog:
    """
    34.24: Compute data quality score for a factory on a given date.
    Score = weighted average of completeness, freshness, validity, device_coverage.
    """
    from app.models.device import Device

    # Get active devices
    devices = db.query(Device).filter(
        Device.factory_id == factory_id,
        Device.is_active == True,
    ).all()

    total_devices = len(devices)
    if total_devices == 0:
        return DataQualityLog(
            factory_id=factory_id,
            date=date_str,
            score=0,
            completeness=0.0,
            freshness=0.0,
            validity=0.0,
            device_coverage=0.0,
            created_at=datetime.now(timezone.utc),
        )

    # Device coverage: how many devices have recent data
    now = datetime.now(timezone.utc)
    online_devices = sum(1 for d in devices if d.last_seen_at and (now - d.last_seen_at) < timedelta(minutes=15))
    device_coverage = online_devices / total_devices if total_devices > 0 else 0.0

    # Freshness: average data age
    ages = []
    for d in devices:
        if d.last_seen_at:
            age_minutes = (now - d.last_seen_at).total_seconds() / 60
            ages.append(min(age_minutes, 60))  # Cap at 60 min
    avg_age = sum(ages) / len(ages) if ages else 60
    freshness = max(0, 1.0 - (avg_age / 60))  # 0=old, 1=fresh

    # Validity: percentage of GOOD quality records (sample last hour)
    one_hour_ago = now - timedelta(hours=1)
    device_ids = [d.id for d in devices]
    if device_ids:
        total_records = (
            db.query(DeviceTelemetry)
            .filter(
                DeviceTelemetry.device_id.in_(device_ids),
                DeviceTelemetry.timestamp >= one_hour_ago,
            )
            .count()
        )
        good_records = (
            db.query(DeviceTelemetry)
            .filter(
                DeviceTelemetry.device_id.in_(device_ids),
                DeviceTelemetry.timestamp >= one_hour_ago,
                DeviceTelemetry.quality == QUALITY_GOOD,
            )
            .count()
        )
        validity = good_records / total_records if total_records > 0 else 0.0
    else:
        validity = 0.0

    # Completeness: rough estimate based on expected vs actual records
    completeness = device_coverage * freshness  # Simplified

    # Weighted score
    score = int(
        completeness * 25
        + freshness * 30
        + validity * 25
        + device_coverage * 20
    )
    score = max(0, min(100, score))

    quality_log = DataQualityLog(
        factory_id=factory_id,
        date=date_str,
        score=score,
        completeness=round(completeness, 3),
        freshness=round(freshness, 3),
        validity=round(validity, 3),
        device_coverage=round(device_coverage, 3),
        created_at=now,
    )
    return quality_log
