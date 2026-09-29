from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, get_all_factories, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.failure_prediction.service import assess_factory, fetch_weather

JOB_NAME = "assess_failure_risk"


async def assess_failure_risk() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        failed_factory_ids = []
        for factory in get_all_factories(db):
            try:
                # Weather failing only costs the ML part (no irradiance ->
                # ml_status NO_IRRADIANCE); rule indicators still run.
                weather = await fetch_weather(factory)
                assess_factory(db, factory, weather)
            except Exception:
                db.rollback()
                failed_factory_ids.append(factory.id)

        if failed_factory_ids:
            finish_job_run(
                db,
                job_run,
                status="failed",
                error_message=f"Failure-risk assessment failed for factories: {failed_factory_ids}",
            )
        else:
            finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_failure_prediction_jobs() -> None:
    # Every 15 minutes: the model's native step, so each run scores one
    # new 15-minute bin.
    scheduler.add_job(
        assess_failure_risk,
        "interval",
        minutes=15,
        id="assess_failure_risk",
        replace_existing=True,
    )
