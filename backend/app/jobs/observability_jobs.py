import logging

from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.observability.anomaly_detection import detect_energy_anomalies
from app.modules.observability.metrics_snapshot import record_system_metric_snapshots
from app.modules.observability.synthetic_monitoring import run_synthetic_checks

logger = logging.getLogger(__name__)


def snapshot_system_metrics() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, "snapshot_system_metrics")

    try:
        count = record_system_metric_snapshots(db)
        logger.info("wrote %d system metric snapshot rows", count)
        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def detect_anomalies() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, "detect_energy_anomalies")

    try:
        count = detect_energy_anomalies(db)
        logger.info("flagged %d new energy anomalies", count)
        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


async def synthetic_monitoring_check() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, "synthetic_monitoring_check")

    try:
        results = await run_synthetic_checks(db)
        failures = [r["name"] for r in results if not r["success"]]

        if failures:
            logger.warning("synthetic check(s) failed: %s", failures)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_observability_jobs() -> None:
    scheduler.add_job(
        snapshot_system_metrics,
        "interval",
        minutes=5,
        id="snapshot_system_metrics",
        replace_existing=True,
    )
    # Runs against yesterday's now-final EnergyDaily row, well after
    # the aggregation job (app/jobs/aggregation_jobs.py) has produced
    # it for the day — 04:00 gives that job a wide margin to finish.
    scheduler.add_job(
        detect_anomalies,
        "cron",
        hour=4,
        minute=0,
        id="detect_energy_anomalies",
        replace_existing=True,
    )
    scheduler.add_job(
        synthetic_monitoring_check,
        "interval",
        minutes=2,
        id="synthetic_monitoring_check",
        replace_existing=True,
    )
