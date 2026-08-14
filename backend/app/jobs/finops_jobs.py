import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.metrics import flush_and_reset_org_metrics
from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.models.organization import Organization
from app.modules.admin.models import APIUsageMetric
from app.modules.finops.service import check_budget_thresholds
from app.modules.finops.storage import get_table_sizes_bytes
from app.modules.monitoring.models import MonitoringIncident
from app.modules.performance.models import CapacityMetric
from app.modules.system.service import get_database_pool_stats

logger = logging.getLogger(__name__)

FLUSH_INTERVAL_MINUTES = 60


def flush_api_usage_metrics() -> None:
    """78: APIUsageMetric (Step 46) existed with no writer — this
    drains the in-memory per-org buckets app.core.metrics accumulates
    via record_org_request and turns each into a persisted row."""
    db = SessionLocal()
    job_run = start_job_run(db, "flush_api_usage_metrics")

    try:
        now = datetime.now(timezone.utc)
        period_start = now - timedelta(minutes=FLUSH_INTERVAL_MINUTES)

        snapshot = flush_and_reset_org_metrics()
        written = 0

        # Guard against a stale org_id (deleted between request-time and
        # flush-time) taking the whole batch down with it — one bad FK
        # would roll back every other organization's usage for this
        # period along with it.
        candidate_org_ids = {org_id for (org_id, _, _) in snapshot.keys()}
        valid_org_ids = set(
            db.scalars(select(Organization.id).where(Organization.id.in_(candidate_org_ids)))
        )

        for (organization_id, endpoint, method), stats in snapshot.items():
            if stats.request_count == 0 or organization_id not in valid_org_ids:
                continue

            avg_latency_ms = round(stats.total_duration_ms / stats.request_count)

            db.add(
                APIUsageMetric(
                    organization_id=organization_id,
                    endpoint=endpoint[:200],
                    method=method,
                    request_count=stats.request_count,
                    error_count=stats.error_count,
                    avg_latency_ms=avg_latency_ms,
                    period_start=period_start,
                    period_end=now,
                )
            )
            written += 1

        db.commit()
        logger.info("wrote %d api_usage_metrics rows", written)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def snapshot_capacity_metrics() -> None:
    """78: CapacityMetric (Step 51) existed with no writer either — real
    measurements against the thresholds already defined on the table's
    warning_threshold/critical_threshold columns.

    84 fix: pool_capacity previously used pool_stats["overflow"], which
    is SQLAlchemy's `checked_out - pool_size` (see get_database_pool_
    stats's docstring) — not the configured overflow ceiling. That made
    current_capacity collapse to ~=checked_out, so every snapshot ever
    taken read as "100% full" regardless of real headroom, and Step 84's
    new alerting job (which finally checks these thresholds for the
    first time) opened a false CRITICAL incident from it immediately."""
    db = SessionLocal()
    job_run = start_job_run(db, "snapshot_capacity_metrics")

    try:
        now = datetime.now(timezone.utc)
        pool_stats = get_database_pool_stats()
        table_sizes = get_table_sizes_bytes(db)

        pool_capacity = float(pool_stats["pool_size"] + pool_stats["max_overflow"])
        db.add(
            CapacityMetric(
                metric="database_connections",
                current_value=float(pool_stats["checked_out"]),
                current_capacity=pool_capacity,
                warning_threshold=pool_capacity * 0.8,
                critical_threshold=pool_capacity * 0.95,
                unit="count",
                measured_at=now,
            )
        )

        total_storage_bytes = sum(table_sizes.values())
        capacity_bytes = settings.DATABASE_STORAGE_CAPACITY_GB * 1024**3
        db.add(
            CapacityMetric(
                metric="high_volume_table_storage_bytes",
                current_value=float(total_storage_bytes),
                current_capacity=capacity_bytes,
                warning_threshold=capacity_bytes * 0.8,
                critical_threshold=capacity_bytes * 0.95,
                unit="bytes",
                measured_at=now,
            )
        )

        db.commit()
        logger.info(
            "snapshotted capacity metrics: db_connections=%s/%s storage=%.1fMB",
            pool_stats["checked_out"],
            pool_capacity,
            total_storage_bytes / 1024 / 1024,
        )

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def check_budget_alerts() -> None:
    """78: Budget Alerts — opens a MonitoringIncident (same reuse
    pattern as app.modules.security.correlation, Step 79) when known
    infra spend crosses a configured BudgetThreshold. Dedup follows the
    same "don't open a second incident while one's already OPEN" rule."""
    db = SessionLocal()
    job_run = start_job_run(db, "check_budget_alerts")

    try:
        breaches = check_budget_thresholds(db)
        opened = 0

        for breach in breaches:
            dedup_key = f"BUDGET_THRESHOLD:{breach['threshold_id']}"
            already_open = (
                db.scalar(
                    select(MonitoringIncident.id).where(
                        MonitoringIncident.service == "finops",
                        MonitoringIncident.title.like(f"%{dedup_key}%"),
                        MonitoringIncident.status.in_(["OPEN", "ACKNOWLEDGED", "INVESTIGATING"]),
                    )
                )
                is not None
            )
            if already_open:
                continue

            now = datetime.now(timezone.utc)
            db.add(
                MonitoringIncident(
                    title=f"Budget threshold breached: {breach['name']} ({dedup_key})",
                    severity=breach["severity"],
                    status="OPEN",
                    service="finops",
                    started_at=now,
                    root_cause=(
                        f"Estimated monthly cost ${breach['current_cost_usd']:.2f} is "
                        f"{breach['percent_used']}% of the ${breach['monthly_budget_usd']:.2f} budget"
                    ),
                    created_at=now,
                )
            )
            opened += 1

        db.commit()
        if opened:
            logger.warning("opened %d budget threshold incident(s)", opened)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_finops_jobs() -> None:
    scheduler.add_job(
        flush_api_usage_metrics,
        "interval",
        minutes=FLUSH_INTERVAL_MINUTES,
        id="flush_api_usage_metrics",
        replace_existing=True,
    )
    scheduler.add_job(
        snapshot_capacity_metrics,
        "interval",
        minutes=15,
        id="snapshot_capacity_metrics",
        replace_existing=True,
    )
    scheduler.add_job(
        check_budget_alerts,
        "interval",
        hours=6,
        id="check_budget_alerts",
        replace_existing=True,
    )
