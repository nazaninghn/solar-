from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler

JOB_NAME = "update_electricity_prices"


def update_electricity_prices() -> None:
    """
    Deliberately a no-op. Step 10 (10.27-10.28) explicitly deferred
    building a real electricity price provider — prices are entered
    manually via POST /electricity-prices for now. This job is still
    registered (rather than omitted) so the schedule stays structurally
    complete per 13.27, and logs itself as "skipped" rather than
    pretending to fetch data that has nowhere real to come from.
    """
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    finish_job_run(
        db,
        job_run,
        status="skipped",
        error_message=(
            "No electricity price provider is configured yet "
            "(Step 10 deferred this)."
        ),
    )

    db.close()


def register_pricing_jobs() -> None:
    scheduler.add_job(
        update_electricity_prices,
        "interval",
        hours=1,
        id="update_electricity_prices",
        replace_existing=True,
    )
