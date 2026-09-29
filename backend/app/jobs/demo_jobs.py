from app.core.config import settings
from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.demo import seed

JOB_NAME = "feed_demo_telemetry"


def feed_demo_telemetry() -> None:
    """Stand-in for the demo factory's devices pushing live readings.
    The regular hourly aggregation job picks them up like any others."""
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)
    try:
        factory = seed.get_demo_factory(db)
        if factory is None:
            finish_job_run(db, job_run, status="skipped", error_message="No demo factory seeded")
            return
        seed.extend_to_now(db, factory, seed.spec_for(db, factory))
        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error)[:500])
        raise
    finally:
        db.close()


def register_demo_jobs() -> None:
    if not settings.DEMO_TELEMETRY_ENABLED:
        return
    scheduler.add_job(
        feed_demo_telemetry, "interval", minutes=5, id=JOB_NAME, replace_existing=True,
    )
