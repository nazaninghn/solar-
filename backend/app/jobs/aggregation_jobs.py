from datetime import datetime, timedelta, timezone

from app.database.session import SessionLocal
from app.energy.balance import check_energy_balance
from app.jobs.common import finish_job_run, get_all_factories, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.energy.aggregation import (
    aggregate_factory_day,
    aggregate_factory_hour,
    aggregate_factory_month,
    sync_device_readings_to_energy_reading,
)
from app.modules.notifications.engine import notify_energy_balance_error

HOURLY_JOB_NAME = "aggregate_hourly_energy"
DAILY_JOB_NAME = "aggregate_daily_energy"
MONTHLY_JOB_NAME = "aggregate_monthly_energy"


def aggregate_hourly_energy() -> None:
    """Aggregates the most recently completed hour for every factory."""
    db = SessionLocal()
    job_run = start_job_run(db, HOURLY_JOB_NAME)

    try:
        now = datetime.now(timezone.utc)
        last_hour_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(
            hours=1
        )

        factories = get_all_factories(db)

        for factory in factories:
            # Must run before aggregate_factory_hour — it derives an
            # EnergyReading row from this hour's DeviceEnergyReading
            # samples, which aggregate_factory_hour then sums alongside
            # any manual entries.
            device_reading = sync_device_readings_to_energy_reading(
                db, factory.id, last_hour_start
            )

            if device_reading:
                violation = check_energy_balance(device_reading)
                if violation:
                    notify_energy_balance_error(db, factory, **violation)

            aggregate_factory_hour(db, factory.id, last_hour_start)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def aggregate_daily_energy() -> None:
    """Aggregates yesterday (the most recently completed day) for every factory."""
    db = SessionLocal()
    job_run = start_job_run(db, DAILY_JOB_NAME)

    try:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        factories = get_all_factories(db)

        for factory in factories:
            aggregate_factory_day(db, factory.id, yesterday)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def aggregate_monthly_energy() -> None:
    """
    Aggregates the current month-to-date for every factory. Runs daily
    (not just once a month) so the current month's figures stay fresh
    for dashboards without waiting for the month to fully close.
    """
    db = SessionLocal()
    job_run = start_job_run(db, MONTHLY_JOB_NAME)

    try:
        month_start = datetime.now(timezone.utc).date().replace(day=1)
        factories = get_all_factories(db)

        for factory in factories:
            aggregate_factory_month(db, factory.id, month_start)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_aggregation_jobs() -> None:
    scheduler.add_job(
        aggregate_hourly_energy,
        "cron",
        minute=5,
        id="aggregate_hourly_energy",
        replace_existing=True,
    )

    scheduler.add_job(
        aggregate_daily_energy,
        "cron",
        hour=1,
        minute=0,
        id="aggregate_daily_energy",
        replace_existing=True,
    )

    scheduler.add_job(
        aggregate_monthly_energy,
        "cron",
        hour=1,
        minute=30,
        id="aggregate_monthly_energy",
        replace_existing=True,
    )
