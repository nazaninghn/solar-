from app.database.session import SessionLocal
from app.forecast.service import generate_and_store_solar_forecast
from app.jobs.common import finish_job_run, get_all_factories, start_job_run
from app.jobs.retry import with_retry
from app.jobs.scheduler import scheduler

JOB_NAME = "generate_solar_forecasts"


async def generate_solar_forecasts() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        factories = get_all_factories(db)
        generated = 0
        failed_factory_ids = []

        for factory in factories:
            if factory.latitude is None or factory.longitude is None:
                continue
            if not factory.solar_capacity_kw:
                continue

            try:
                # 25.23-25.25: retried per-factory, not job-wide — one
                # factory's weather provider hiccup shouldn't cost every
                # other factory in the batch their own forecast, and the
                # upsert-by-unique-constraint pattern this already relies
                # on makes retrying the whole fetch+persist safe.
                await with_retry(
                    lambda f=factory: generate_and_store_solar_forecast(db, f)
                )
                generated += 1
            except Exception:
                failed_factory_ids.append(factory.id)

        if failed_factory_ids:
            finish_job_run(
                db,
                job_run,
                status="failed",
                error_message=(
                    f"{len(failed_factory_ids)} of {generated + len(failed_factory_ids)} "
                    f"factories failed after retries: {failed_factory_ids}"
                ),
            )
        else:
            finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_solar_forecast_jobs() -> None:
    # 25.33: cron on fixed hours, not "interval, hours=6" — an interval
    # schedule's actual fire times drift with whenever the process last
    # started, so there's no guarantee a fresh forecast exists by the
    # time someone opens the dashboard in the morning. Anchoring to
    # 00:00/06:00/12:00/18:00 guarantees a 06:00 run without needing a
    # separate "morning job" orchestrator.
    scheduler.add_job(
        generate_solar_forecasts,
        "cron",
        hour="0,6,12,18",
        minute=0,
        id="generate_solar_forecasts",
        replace_existing=True,
    )
