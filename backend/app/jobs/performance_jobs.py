import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.metrics import get_request_metrics_snapshot
from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.monitoring.models import MonitoringIncident
from app.modules.performance.models import CapacityMetric

logger = logging.getLogger(__name__)

# 84: docs/operations/scalability.md already defines "P95 > 2x target ->
# Investigate + scale" as the scaling trigger, and "Dashboard <500ms" as
# the P95 target for this platform's most common read path — reused
# here rather than inventing a second set of numbers. 500ms * 2 = 1000ms,
# which also happens to line up with RequestLoggingMiddleware's own
# "slow" bucket threshold (app/core/middleware.py).
P95_ALERT_THRESHOLD_MS = 1000.0
# scalability.md's per-endpoint max error rates are 0.5-1%; 5% globally
# (across every endpoint, not just the strictest one) is the point
# where this is clearly systemic rather than one flaky dependency.
ERROR_RATE_ALERT_THRESHOLD_PCT = 5.0

# 84: snapshot_capacity_metrics (finops_jobs.py) runs every 15 minutes —
# a row older than double that has missed at least one cycle, which in
# practice means the scheduler wasn't running (e.g. between dev-server
# restarts) rather than a real, current breach. Alerting on a stale row
# would be a false positive dressed up as real data.
CAPACITY_METRIC_STALENESS_MINUTES = 30


def check_performance_thresholds() -> None:
    """84: closes two real gaps found during this step's own load test:
    (1) /api/v1/system/metrics already computes real P50/P95/P99 and
    error rate (Step 77) but nothing ever alerted on it; (2)
    CapacityMetric (Step 78) computes warning_threshold/critical_
    threshold per row but nothing ever checked current_value against
    them. Both now feed the same MonitoringIncident pattern as every
    other alert job this session (Steps 78-83)."""
    db = SessionLocal()
    job_run = start_job_run(db, "check_performance_thresholds")

    try:
        opened = 0
        snapshot = get_request_metrics_snapshot()

        if snapshot["total_requests"] > 0:
            if snapshot["p95_duration_ms"] > P95_ALERT_THRESHOLD_MS:
                opened += _open_incident(
                    db,
                    dedup_key="LATENCY_P95",
                    title="Request P95 latency exceeds threshold",
                    root_cause=(
                        f"P95 latency is {snapshot['p95_duration_ms']:.0f}ms, "
                        f"above the {P95_ALERT_THRESHOLD_MS:.0f}ms threshold "
                        f"(2x the documented Dashboard target)"
                    ),
                    severity="WARNING",
                )

            if snapshot["error_rate_percent"] > ERROR_RATE_ALERT_THRESHOLD_PCT:
                opened += _open_incident(
                    db,
                    dedup_key="ERROR_RATE",
                    title="Request error rate exceeds threshold",
                    root_cause=(
                        f"5xx error rate is {snapshot['error_rate_percent']:.1f}%, "
                        f"above the {ERROR_RATE_ALERT_THRESHOLD_PCT:.0f}% threshold"
                    ),
                    severity="CRITICAL" if snapshot["error_rate_percent"] > 20 else "WARNING",
                )

        staleness_cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=CAPACITY_METRIC_STALENESS_MINUTES
        )
        latest_by_metric: dict[str, CapacityMetric] = {}
        for metric in db.scalars(
            select(CapacityMetric).order_by(CapacityMetric.measured_at.desc()).limit(50)
        ):
            latest_by_metric.setdefault(metric.metric, metric)

        for metric_name, metric in latest_by_metric.items():
            if metric.measured_at < staleness_cutoff:
                logger.info(
                    "skipping capacity check for %s: latest reading is stale (measured_at=%s)",
                    metric_name, metric.measured_at,
                )
                continue
            if metric.critical_threshold is not None and metric.current_value >= metric.critical_threshold:
                opened += _open_incident(
                    db,
                    dedup_key=f"CAPACITY_CRITICAL:{metric_name}",
                    title=f"Capacity critical: {metric_name}",
                    root_cause=(
                        f"{metric_name} at {metric.current_value:.0f} / "
                        f"{metric.current_capacity:.0f} {metric.unit} "
                        f"({metric.current_value / metric.current_capacity * 100:.0f}%), "
                        f"above the critical threshold of {metric.critical_threshold:.0f}"
                    ),
                    severity="CRITICAL",
                )
            elif metric.warning_threshold is not None and metric.current_value >= metric.warning_threshold:
                opened += _open_incident(
                    db,
                    dedup_key=f"CAPACITY_WARNING:{metric_name}",
                    title=f"Capacity warning: {metric_name}",
                    root_cause=(
                        f"{metric_name} at {metric.current_value:.0f} / "
                        f"{metric.current_capacity:.0f} {metric.unit} "
                        f"({metric.current_value / metric.current_capacity * 100:.0f}%), "
                        f"above the warning threshold of {metric.warning_threshold:.0f}"
                    ),
                    severity="WARNING",
                )

        if opened:
            logger.warning("opened %d performance incident(s)", opened)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def _open_incident(db, dedup_key: str, title: str, root_cause: str, severity: str) -> int:
    already_open = (
        db.scalar(
            select(MonitoringIncident.id).where(
                MonitoringIncident.service == "performance",
                MonitoringIncident.title.like(f"%{dedup_key}%"),
                MonitoringIncident.status.in_(["OPEN", "ACKNOWLEDGED", "INVESTIGATING"]),
            )
        )
        is not None
    )
    if already_open:
        return 0

    now = datetime.now(timezone.utc)
    db.add(
        MonitoringIncident(
            title=f"{title} ({dedup_key})",
            severity=severity,
            status="OPEN",
            service="performance",
            started_at=now,
            root_cause=root_cause,
            created_at=now,
        )
    )
    db.commit()
    return 1


def register_performance_jobs() -> None:
    scheduler.add_job(
        check_performance_thresholds,
        "interval",
        minutes=10,
        id="check_performance_thresholds",
        replace_existing=True,
    )
