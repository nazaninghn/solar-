import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.models.device_energy_reading import DeviceEnergyReading

logger = logging.getLogger(__name__)

JOB_NAME = "purge_old_telemetry"

# 26.27: "مقادیر دقیق را بعداً بر اساس هزینه Database تعیین می‌کنیم" —
# a provisional default, tunable later. Scoped to DeviceEnergyReading
# only (the per-device raw table growing at polling-cadence rates,
# 26.17's "52 million+ rows/year" concern) — EnergyReading/Hourly/Daily/
# Monthly are already coarser aggregates meant to be kept for years and
# are orders of magnitude lower volume.
RAW_TELEMETRY_RETENTION_DAYS = 90


def purge_old_telemetry() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=RAW_TELEMETRY_RETENTION_DAYS)

        result = db.execute(
            delete(DeviceEnergyReading).where(DeviceEnergyReading.timestamp < cutoff)
        )
        deleted_count = result.rowcount

        db.commit()

        logger.info(
            "purged %d device_energy_readings rows older than %s",
            deleted_count,
            cutoff.isoformat(),
        )

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_retention_jobs() -> None:
    scheduler.add_job(
        purge_old_telemetry,
        "cron",
        hour=2,
        minute=30,
        id="purge_old_telemetry",
        replace_existing=True,
    )
