from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, get_all_factories, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.recommendations.service import generate_factory_recommendations

JOB_NAME = "generate_recommendations"


async def generate_recommendations_for_factories() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        factories = get_all_factories(db)

        for factory in factories:
            await generate_factory_recommendations(db, factory)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_recommendation_jobs() -> None:
    # 13.27's schedule table lists Recommendations as hourly; 13.14's
    # narrative example shows it once at 02:30 as part of the nightly
    # chain instead. Followed the table since it's presented as the
    # actual recommended schedule, and hourly matches Step 11's own
    # point about not waiting for a dashboard visit.
    scheduler.add_job(
        generate_recommendations_for_factories,
        "interval",
        hours=1,
        id="generate_recommendations",
        replace_existing=True,
    )
