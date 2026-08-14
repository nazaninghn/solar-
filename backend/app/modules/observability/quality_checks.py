"""
STEP 41.3-41.14: Data Quality Checks.

Freshness, completeness, validity, energy balance, outlier detection.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.device import Device
from app.modules.observability.models import DQ_DEGRADED, DQ_GOOD, DQ_STALE, DQ_UNAVAILABLE, DataQualityEvent
from app.modules.pipeline.models import DailyEnergySummary

logger = logging.getLogger(__name__)


def check_telemetry_freshness(
    db: Session, factory_id: int, threshold_seconds: int = 300
) -> dict:
    """41.5: Check how fresh telemetry data is for each device."""
    now = datetime.now(timezone.utc)
    devices = db.query(Device).filter(
        Device.factory_id == factory_id, Device.is_active == True
    ).all()

    results = []
    for device in devices:
        if not device.last_seen_at:
            status = DQ_UNAVAILABLE
            age_seconds = None
        else:
            age_seconds = (now - device.last_seen_at).total_seconds()
            if age_seconds < threshold_seconds:
                status = DQ_GOOD
            elif age_seconds < threshold_seconds * 2:
                status = DQ_DEGRADED
            else:
                status = DQ_STALE

        results.append({
            "device_id": device.id,
            "name": device.name,
            "status": status,
            "age_seconds": age_seconds,
            "last_seen_at": device.last_seen_at,
        })

    return {"factory_id": factory_id, "devices": results}


def check_energy_balance(
    db: Session,
    factory_id: int,
    date_str: str,
    tolerance_pct: float = 10.0,
) -> dict:
    """
    41.12: Energy Balance Check.
    Solar + Import + Battery_Discharge ≈ Consumption + Charge + Export + Losses
    """
    summary = db.query(DailyEnergySummary).filter(
        DailyEnergySummary.factory_id == factory_id,
        DailyEnergySummary.date == date_str,
    ).first()

    if not summary:
        return {"factory_id": factory_id, "date": date_str, "is_valid": True, "reason": "no_data"}

    supply = summary.solar_generation_kwh + summary.grid_import_kwh + summary.battery_discharge_kwh
    demand = summary.factory_consumption_kwh + summary.battery_charge_kwh + summary.grid_export_kwh

    balance_error = abs(supply - demand)
    tolerance = max(supply, demand) * (tolerance_pct / 100.0) if max(supply, demand) > 0 else 50.0
    is_valid = balance_error <= tolerance

    if not is_valid:
        logger.warning(
            f"Energy balance mismatch factory {factory_id} date {date_str}: "
            f"supply={supply:.1f} demand={demand:.1f} error={balance_error:.1f} tolerance={tolerance:.1f}"
        )
        # Create quality event
        db.add(DataQualityEvent(
            factory_id=factory_id,
            source_type="energy_balance",
            issue_type="ENERGY_BALANCE_MISMATCH",
            severity="HIGH",
            observed_value=balance_error,
            expected_value=tolerance,
            description=f"Supply={supply:.1f}kWh, Demand={demand:.1f}kWh, Error={balance_error:.1f}kWh",
            started_at=datetime.now(timezone.utc),
        ))
        db.commit()

    return {
        "factory_id": factory_id,
        "date": date_str,
        "solar_kwh": summary.solar_generation_kwh,
        "grid_import_kwh": summary.grid_import_kwh,
        "battery_discharge_kwh": summary.battery_discharge_kwh,
        "consumption_kwh": summary.factory_consumption_kwh,
        "battery_charge_kwh": summary.battery_charge_kwh,
        "grid_export_kwh": summary.grid_export_kwh,
        "balance_error_kwh": round(balance_error, 2),
        "tolerance_kwh": round(tolerance, 2),
        "is_valid": is_valid,
    }


def detect_outlier(metric: str, value: float, device_capacity: float | None = None) -> bool:
    """41.9: Basic outlier detection."""
    static_ranges = {
        "soc": (0, 100),
        "temperature_c": (-40, 80),
        "power_kw": (-5000, 5000),
        "voltage": (0, 1500),
    }

    if metric in static_ranges:
        min_v, max_v = static_ranges[metric]
        if value < min_v or value > max_v:
            return True

    # Device-specific: power shouldn't exceed 2.5x capacity
    if device_capacity and metric == "power_kw":
        if abs(value) > device_capacity * 2.5:
            return True

    return False


def compute_factory_quality_score(
    db: Session, factory_id: int
) -> dict:
    """41.4: Weighted quality score for a factory."""
    now = datetime.now(timezone.utc)

    devices = db.query(Device).filter(
        Device.factory_id == factory_id, Device.is_active == True
    ).all()

    if not devices:
        return {"score": 0, "status": DQ_UNAVAILABLE, "details": "No active devices"}

    # Freshness (weight: 35%)
    fresh_count = sum(
        1 for d in devices
        if d.last_seen_at and (now - d.last_seen_at).total_seconds() < 300
    )
    freshness = fresh_count / len(devices) if devices else 0

    # Completeness (weight: 30%) — devices reporting data
    reporting = sum(1 for d in devices if d.last_seen_at is not None)
    completeness = reporting / len(devices) if devices else 0

    # Availability (weight: 20%)
    online = sum(1 for d in devices if d.status == "ONLINE")
    availability = online / len(devices) if devices else 0

    # No recent errors (weight: 15%)
    error_free = sum(1 for d in devices if d.consecutive_error_count == 0)
    validity = error_free / len(devices) if devices else 0

    score = int(freshness * 35 + completeness * 30 + availability * 20 + validity * 15)
    score = max(0, min(100, score))

    if score >= 80:
        status = DQ_GOOD
    elif score >= 50:
        status = DQ_DEGRADED
    else:
        status = DQ_STALE

    return {
        "score": score,
        "status": status,
        "freshness": round(freshness, 3),
        "completeness": round(completeness, 3),
        "availability": round(availability, 3),
        "validity": round(validity, 3),
    }
