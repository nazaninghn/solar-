from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.models.device import Device

JOB_NAME = "check_device_health"

# Same 15-minute threshold app/modules/notifications/engine.py's
# _get_offline_devices already uses for alerting — this job's job is to
# make Device.status itself reflect that reality (26.6: OFFLINE was
# never actually persisted anywhere before this), not to introduce a
# second, different definition of "offline".
OFFLINE_THRESHOLD_MINUTES = 15


def check_device_health() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=OFFLINE_THRESHOLD_MINUTES)

        stale_devices = db.scalars(
            select(Device).where(
                Device.is_active.is_(True),
                Device.status != "OFFLINE",
                (Device.last_seen_at.is_(None)) | (Device.last_seen_at < cutoff),
            )
        ).all()

        for device in stale_devices:
            device.status = "OFFLINE"

        db.commit()

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_device_health_jobs() -> None:
    scheduler.add_job(
        check_device_health,
        "interval",
        minutes=5,
        id="check_device_health",
        replace_existing=True,
    )
