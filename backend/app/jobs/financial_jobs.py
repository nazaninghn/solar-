from datetime import datetime, timedelta, timezone

from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, get_all_factories, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.financial.service import compute_daily_financial_record

JOB_NAME = "calculate_daily_financials"


def calculate_daily_financials() -> None:
    """
    Finalizes yesterday's FinancialRecord for every factory. Runs once
    the day is fully over so the day's EnergyReading/ElectricityPrice
    data is complete, rather than trying to close out "today" mid-day.
    compute_daily_financial_record already upserts by (factory_id, date)
    (12.1's unique constraint), so re-running this is safe.
    """
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        factories = get_all_factories(db)

        for factory in factories:
            compute_daily_financial_record(db, factory.id, yesterday)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_financial_jobs() -> None:
    scheduler.add_job(
        calculate_daily_financials,
        "cron",
        hour=3,
        minute=0,
        id="daily_financials",
        replace_existing=True,
    )
