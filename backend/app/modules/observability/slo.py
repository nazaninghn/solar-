"""
STEP 77.25-77.28: SLI/SLO/error budget as computable data, not just the
table in docs/operations/observability-overview.md. Targets below are
transcribed from that doc verbatim — this module is what actually
evaluates them against live data.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.metrics import get_request_metrics_snapshot
from app.models.device import Device
from app.models.device_energy_reading import DeviceEnergyReading
from app.models.job_run import JobRun

_EVALUATION_WINDOW_HOURS = 24


def _availability_slo(name: str, sli_description: str, actual_percent: float, target_percent: float) -> dict:
    allowed_failure_percent = 100 - target_percent
    actual_failure_percent = max(0.0, 100 - actual_percent)

    # 77.28: Allowed Failure = Error Budget. >100% means the budget for
    # this window is already blown, not just "low" — deliberately not
    # clamped to 100 so that overrun is visible rather than hidden.
    budget_consumed_percent = (
        round((actual_failure_percent / allowed_failure_percent) * 100, 1)
        if allowed_failure_percent > 0
        else 0.0
    )

    return {
        "name": name,
        "sli": sli_description,
        "actual_value": round(actual_percent, 2),
        "target_value": target_percent,
        "unit": "percent",
        "compliant": actual_percent >= target_percent,
        "error_budget_consumed_percent": budget_consumed_percent,
    }


def _ceiling_slo(name: str, sli_description: str, actual_value: float, target_value: float, unit: str) -> dict:
    """For SLOs where lower is better (latency, freshness) — no error
    budget concept applied here since it doesn't map onto a pass/fail
    count the way an availability ratio does."""
    return {
        "name": name,
        "sli": sli_description,
        "actual_value": round(actual_value, 2),
        "target_value": target_value,
        "unit": unit,
        "compliant": actual_value <= target_value,
    }


def compute_slo_status(db: Session) -> list[dict]:
    window_start = datetime.now(timezone.utc) - timedelta(hours=_EVALUATION_WINDOW_HOURS)
    request_metrics = get_request_metrics_snapshot()

    results = []

    # API Availability >= 99.5%
    results.append(
        _availability_slo(
            "api_availability",
            "Successful requests / Total",
            100 - request_metrics["error_rate_percent"],
            99.5,
        )
    )

    # API Latency: P95 <= 500ms
    results.append(
        _ceiling_slo(
            "api_latency_p95",
            "P95 response time",
            request_metrics["p95_duration_ms"],
            500,
            "ms",
        )
    )

    # Telemetry Ingest >= 99% — GOOD vs total DeviceEnergyReading rows
    # in the evaluation window (31.19-31.20's data_quality flag is
    # exactly "did this reading pass validation").
    quality_counts = db.execute(
        select(
            DeviceEnergyReading.data_quality, func.count()
        ).where(
            DeviceEnergyReading.timestamp >= window_start
        ).group_by(DeviceEnergyReading.data_quality)
    ).all()
    total_readings = sum(count for _, count in quality_counts)
    good_readings = sum(count for quality, count in quality_counts if quality == "GOOD")
    ingest_rate = (good_readings / total_readings * 100) if total_readings else 100.0

    results.append(
        _availability_slo(
            "telemetry_ingest",
            "Successful ingestion rate",
            ingest_rate,
            99.0,
        )
    )

    # Queue Processing >= 99% — JobRun success rate in the window.
    job_counts = db.execute(
        select(JobRun.status, func.count()).where(
            JobRun.started_at >= window_start
        ).group_by(JobRun.status)
    ).all()
    total_jobs = sum(count for _, count in job_counts)
    successful_jobs = sum(count for status_value, count in job_counts if status_value == "success")
    job_success_rate = (successful_jobs / total_jobs * 100) if total_jobs else 100.0

    results.append(
        _availability_slo(
            "queue_processing",
            "Jobs completed / Jobs created",
            job_success_rate,
            99.0,
        )
    )

    # Data Freshness <= 5 min — average age of the latest reading across
    # active devices, same "positive = online" set get_device_status_
    # counts already filters to.
    now = datetime.now(timezone.utc)
    last_seen_values = db.scalars(
        select(Device.last_seen_at).where(
            Device.is_active.is_(True), Device.last_seen_at.isnot(None)
        )
    ).all()
    average_age_minutes = (
        sum((now - ts).total_seconds() / 60 for ts in last_seen_values) / len(last_seen_values)
        if last_seen_values
        else 0.0
    )

    results.append(
        _ceiling_slo(
            "data_freshness",
            "Age of latest telemetry",
            average_age_minutes,
            5,
            "minutes",
        )
    )

    return results
