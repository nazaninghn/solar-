import logging

from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.security.correlation import detect_correlated_security_activity

logger = logging.getLogger(__name__)


def correlate_security_events() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, "correlate_security_events")

    try:
        count = detect_correlated_security_activity(db)
        if count:
            logger.warning("opened %d correlated security incident(s)", count)
        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_security_jobs() -> None:
    scheduler.add_job(
        correlate_security_events,
        "interval",
        minutes=5,
        id="correlate_security_events",
        replace_existing=True,
    )
