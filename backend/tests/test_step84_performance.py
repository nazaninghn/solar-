import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.core.config import settings
from app.database.session import SessionLocal, engine
from app.jobs.finops_jobs import snapshot_capacity_metrics
from app.jobs.performance_jobs import (
    CAPACITY_METRIC_STALENESS_MINUTES,
    ERROR_RATE_ALERT_THRESHOLD_PCT,
    P95_ALERT_THRESHOLD_MS,
    check_performance_thresholds,
)
from app.modules.monitoring.models import MonitoringIncident
from app.modules.performance.models import CapacityMetric
from app.modules.system.service import get_database_pool_stats


def _clear_performance_incidents(db):
    db.query(MonitoringIncident).filter(MonitoringIncident.service == "performance").delete(
        synchronize_session=False
    )
    db.commit()


# --- Connection pool config + the capacity-metric bug fix (84) ---


def test_pool_stats_exposes_configured_max_overflow():
    stats = get_database_pool_stats()
    assert stats["max_overflow"] == settings.DB_MAX_OVERFLOW
    assert stats["pool_size"] == engine.pool.size()


def test_snapshot_capacity_metrics_computes_real_ceiling_not_checked_out():
    """84 bug fix regression test: pool_capacity must equal
    pool_size + max_overflow, not collapse to ~=checked_out via
    SQLAlchemy's pool.overflow() (checked_out - pool_size)."""
    db = SessionLocal()
    try:
        snapshot_capacity_metrics()

        metric = (
            db.query(CapacityMetric)
            .filter(CapacityMetric.metric == "database_connections")
            .order_by(CapacityMetric.measured_at.desc())
            .first()
        )
        assert metric is not None

        expected_capacity = float(settings.DB_POOL_SIZE + settings.DB_MAX_OVERFLOW)
        assert metric.current_capacity == expected_capacity
        # The bug made current_capacity collapse to ~= current_value
        # (checked_out) regardless of real pool size; assert they're
        # genuinely different now that the pool is non-trivially sized.
        assert metric.current_capacity != metric.current_value
    finally:
        db.close()


# --- Performance alerting job (84) ---


def test_check_performance_thresholds_opens_incident_on_high_p95():
    db = SessionLocal()
    try:
        _clear_performance_incidents(db)

        fake_snapshot = {
            "total_requests": 500,
            "error_rate_percent": 0.0,
            "p95_duration_ms": P95_ALERT_THRESHOLD_MS + 500,
        }
        with patch("app.jobs.performance_jobs.get_request_metrics_snapshot", return_value=fake_snapshot):
            check_performance_thresholds()

        incident = (
            db.query(MonitoringIncident)
            .filter(
                MonitoringIncident.service == "performance",
                MonitoringIncident.title.like("%LATENCY_P95%"),
            )
            .first()
        )
        assert incident is not None
        assert incident.severity == "WARNING"
    finally:
        _clear_performance_incidents(db)
        db.close()


def test_check_performance_thresholds_opens_incident_on_high_error_rate():
    db = SessionLocal()
    try:
        _clear_performance_incidents(db)

        fake_snapshot = {
            "total_requests": 500,
            "error_rate_percent": ERROR_RATE_ALERT_THRESHOLD_PCT + 10,
            "p95_duration_ms": 50,
        }
        with patch("app.jobs.performance_jobs.get_request_metrics_snapshot", return_value=fake_snapshot):
            check_performance_thresholds()

        incident = (
            db.query(MonitoringIncident)
            .filter(
                MonitoringIncident.service == "performance",
                MonitoringIncident.title.like("%ERROR_RATE%"),
            )
            .first()
        )
        assert incident is not None
    finally:
        _clear_performance_incidents(db)
        db.close()


def test_check_performance_thresholds_dedups_open_incident():
    db = SessionLocal()
    try:
        _clear_performance_incidents(db)

        fake_snapshot = {
            "total_requests": 500,
            "error_rate_percent": 0.0,
            "p95_duration_ms": P95_ALERT_THRESHOLD_MS + 500,
        }
        with patch("app.jobs.performance_jobs.get_request_metrics_snapshot", return_value=fake_snapshot):
            check_performance_thresholds()
            check_performance_thresholds()

        count = (
            db.query(MonitoringIncident)
            .filter(
                MonitoringIncident.service == "performance",
                MonitoringIncident.title.like("%LATENCY_P95%"),
            )
            .count()
        )
        assert count == 1
    finally:
        _clear_performance_incidents(db)
        db.close()


def test_check_performance_thresholds_ignores_stale_capacity_rows():
    """84: a CapacityMetric row older than 2x the snapshot job's own
    interval must not trigger an alert - this is exactly the false
    positive this step's own testing hit before the staleness guard
    was added."""
    db = SessionLocal()
    metric_id = None
    try:
        _clear_performance_incidents(db)
        db.query(CapacityMetric).delete(synchronize_session=False)
        db.commit()

        stale_time = datetime.now(timezone.utc) - timedelta(
            minutes=CAPACITY_METRIC_STALENESS_MINUTES + 10
        )
        stale_metric = CapacityMetric(
            metric="database_connections",
            current_value=100.0,
            current_capacity=100.0,
            warning_threshold=80.0,
            critical_threshold=95.0,
            unit="count",
            measured_at=stale_time,
        )
        db.add(stale_metric)
        db.commit()
        metric_id = stale_metric.id

        with patch(
            "app.jobs.performance_jobs.get_request_metrics_snapshot",
            return_value={"total_requests": 0, "error_rate_percent": 0.0, "p95_duration_ms": 0.0},
        ):
            check_performance_thresholds()

        incident = (
            db.query(MonitoringIncident)
            .filter(
                MonitoringIncident.service == "performance",
                MonitoringIncident.title.like("%CAPACITY%"),
            )
            .first()
        )
        assert incident is None
    finally:
        if metric_id is not None:
            db.query(CapacityMetric).filter(CapacityMetric.id == metric_id).delete(synchronize_session=False)
        _clear_performance_incidents(db)
        db.commit()
        db.close()


def test_check_performance_thresholds_alerts_on_fresh_critical_capacity():
    db = SessionLocal()
    metric_id = None
    try:
        _clear_performance_incidents(db)

        fresh_metric = CapacityMetric(
            metric=f"pytest_metric_{uuid.uuid4().hex[:8]}",
            current_value=99.0,
            current_capacity=100.0,
            warning_threshold=80.0,
            critical_threshold=95.0,
            unit="count",
            measured_at=datetime.now(timezone.utc),
        )
        db.add(fresh_metric)
        db.commit()
        metric_id = fresh_metric.id

        with patch(
            "app.jobs.performance_jobs.get_request_metrics_snapshot",
            return_value={"total_requests": 0, "error_rate_percent": 0.0, "p95_duration_ms": 0.0},
        ):
            check_performance_thresholds()

        incident = (
            db.query(MonitoringIncident)
            .filter(
                MonitoringIncident.service == "performance",
                MonitoringIncident.title.like(f"%CAPACITY_CRITICAL:{fresh_metric.metric}%"),
            )
            .first()
        )
        assert incident is not None
        assert incident.severity == "CRITICAL"
    finally:
        if metric_id is not None:
            db.query(CapacityMetric).filter(CapacityMetric.id == metric_id).delete(synchronize_session=False)
        _clear_performance_incidents(db)
        db.commit()
        db.close()
