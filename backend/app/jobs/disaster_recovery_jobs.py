import logging

from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.disaster_recovery.service import seed_recovery_targets

logger = logging.getLogger(__name__)


def refresh_recovery_targets() -> None:
    """83: idempotent daily seed — ensures the 6 documented RPO/RTO
    targets exist even on a fresh database, without ever overwriting a
    value an admin has since adjusted (seed_recovery_targets only
    creates missing rows)."""
    db = SessionLocal()
    job_run = start_job_run(db, "refresh_recovery_targets")

    try:
        targets = seed_recovery_targets(db)
        logger.info("recovery targets present: %d", len(targets))
        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_disaster_recovery_jobs() -> None:
    scheduler.add_job(
        refresh_recovery_targets,
        "cron",
        hour=4,
        minute=30,
        id="refresh_recovery_targets",
        replace_existing=True,
    )
