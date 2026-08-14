"""
STEP 34.15-34.22: Aggregation Workers.

Computes 5-minute, hourly, and daily aggregations from normalized telemetry.
Also builds daily energy summaries.
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.device import Device
from app.modules.gateway.models import DeviceTelemetry
from app.modules.pipeline.models import DailyEnergySummary, Telemetry5m, TelemetryHourly

logger = logging.getLogger(__name__)


def aggregate_5m(
    db: Session,
    factory_id: int,
    bucket_start: datetime,
) -> int:
    """
    34.15: Aggregate raw telemetry into 5-minute buckets.
    Returns number of buckets created/updated.
    """
    bucket_end = bucket_start + timedelta(minutes=5)

    device_ids = [
        d.id for d in db.query(Device.id).filter(Device.factory_id == factory_id).all()
    ]
    if not device_ids:
        return 0

    # Query raw data in the bucket window
    results = (
        db.query(
            DeviceTelemetry.device_id,
            DeviceTelemetry.metric,
            func.min(DeviceTelemetry.value).label("min_val"),
            func.max(DeviceTelemetry.value).label("max_val"),
            func.avg(DeviceTelemetry.value).label("avg_val"),
            func.sum(DeviceTelemetry.value).label("sum_val"),
            func.count(DeviceTelemetry.id).label("cnt"),
        )
        .filter(
            DeviceTelemetry.device_id.in_(device_ids),
            DeviceTelemetry.timestamp >= bucket_start,
            DeviceTelemetry.timestamp < bucket_end,
            DeviceTelemetry.quality == "GOOD",
        )
        .group_by(DeviceTelemetry.device_id, DeviceTelemetry.metric)
        .all()
    )

    count = 0
    for row in results:
        # Get last value
        last = (
            db.query(DeviceTelemetry.value)
            .filter(
                DeviceTelemetry.device_id == row.device_id,
                DeviceTelemetry.metric == row.metric,
                DeviceTelemetry.timestamp >= bucket_start,
                DeviceTelemetry.timestamp < bucket_end,
            )
            .order_by(DeviceTelemetry.timestamp.desc())
            .first()
        )

        bucket = Telemetry5m(
            factory_id=factory_id,
            device_id=row.device_id,
            metric=row.metric,
            bucket_start=bucket_start,
            min_value=row.min_val,
            max_value=row.max_val,
            avg_value=row.avg_val,
            sum_value=row.sum_val,
            last_value=last[0] if last else row.avg_val,
            sample_count=row.cnt,
            quality_summary="GOOD",
        )
        db.merge(bucket)  # Upsert (idempotent)
        count += 1

    if count:
        db.commit()
    return count


def aggregate_hourly(
    db: Session,
    factory_id: int,
    hour_start: datetime,
) -> int:
    """34.15: Roll up 5-minute buckets into hourly."""
    hour_end = hour_start + timedelta(hours=1)

    results = (
        db.query(
            Telemetry5m.device_id,
            Telemetry5m.metric,
            func.min(Telemetry5m.min_value).label("min_val"),
            func.max(Telemetry5m.max_value).label("max_val"),
            func.avg(Telemetry5m.avg_value).label("avg_val"),
            func.sum(Telemetry5m.sum_value).label("sum_val"),
            func.sum(Telemetry5m.sample_count).label("cnt"),
        )
        .filter(
            Telemetry5m.factory_id == factory_id,
            Telemetry5m.bucket_start >= hour_start,
            Telemetry5m.bucket_start < hour_end,
        )
        .group_by(Telemetry5m.device_id, Telemetry5m.metric)
        .all()
    )

    count = 0
    for row in results:
        last_bucket = (
            db.query(Telemetry5m.last_value)
            .filter(
                Telemetry5m.factory_id == factory_id,
                Telemetry5m.device_id == row.device_id,
                Telemetry5m.metric == row.metric,
                Telemetry5m.bucket_start >= hour_start,
                Telemetry5m.bucket_start < hour_end,
            )
            .order_by(Telemetry5m.bucket_start.desc())
            .first()
        )

        hourly = TelemetryHourly(
            factory_id=factory_id,
            device_id=row.device_id,
            metric=row.metric,
            bucket_start=hour_start,
            min_value=row.min_val,
            max_value=row.max_val,
            avg_value=row.avg_val,
            sum_value=row.sum_val,
            last_value=last_bucket[0] if last_bucket else row.avg_val,
            sample_count=row.cnt,
            quality_summary="GOOD",
        )
        db.merge(hourly)
        count += 1

    if count:
        db.commit()
    return count


def compute_daily_summary(
    db: Session,
    factory_id: int,
    target_date: date,
) -> DailyEnergySummary:
    """
    34.22: Compute daily energy summary from hourly aggregations.
    Uses power → energy integration (34.16).
    """
    date_str = target_date.isoformat()
    day_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    # Query hourly data for the day
    hourly_data = (
        db.query(TelemetryHourly)
        .filter(
            TelemetryHourly.factory_id == factory_id,
            TelemetryHourly.bucket_start >= day_start,
            TelemetryHourly.bucket_start < day_end,
        )
        .all()
    )

    # Aggregate by metric (avg_value * 1 hour = energy in kWh for power metrics)
    solar_kwh = 0.0
    consumption_kwh = 0.0
    grid_import_kwh = 0.0
    grid_export_kwh = 0.0
    battery_charge_kwh = 0.0
    battery_discharge_kwh = 0.0
    peak_kw = 0.0
    peak_ts = None

    for h in hourly_data:
        if h.metric == "solar_power":
            solar_kwh += abs(h.avg_value)  # Power(kW) × 1h = kWh
        elif h.metric == "load_power":
            consumption_kwh += abs(h.avg_value)
            if h.max_value > peak_kw:
                peak_kw = h.max_value
                peak_ts = h.bucket_start
        elif h.metric == "grid_import_power":
            grid_import_kwh += abs(h.avg_value)
        elif h.metric == "grid_export_power":
            grid_export_kwh += abs(h.avg_value)
        elif h.metric == "battery_power":
            if h.avg_value > 0:
                battery_charge_kwh += h.avg_value
            else:
                battery_discharge_kwh += abs(h.avg_value)

    summary = DailyEnergySummary(
        factory_id=factory_id,
        date=date_str,
        solar_generation_kwh=round(solar_kwh, 2),
        factory_consumption_kwh=round(consumption_kwh, 2),
        grid_import_kwh=round(grid_import_kwh, 2),
        grid_export_kwh=round(grid_export_kwh, 2),
        battery_charge_kwh=round(battery_charge_kwh, 2),
        battery_discharge_kwh=round(battery_discharge_kwh, 2),
        estimated_cost=0.0,  # Calculated by financial engine
        estimated_savings=0.0,
        peak_power_kw=round(peak_kw, 2) if peak_kw > 0 else None,
        peak_timestamp=peak_ts,
        data_quality="GOOD",
        data_quality_score=100,
    )

    db.merge(summary)
    db.commit()
    db.refresh(summary)
    return summary
