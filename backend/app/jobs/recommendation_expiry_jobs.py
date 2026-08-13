from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.recommendations.service import expire_stale_recommendations

JOB_NAME = "expire_stale_recommendations"


def expire_recommendations() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        expired_count = expire_stale_recommendations(db)
        finish_job_run(db, job_run, status="success")
        _ = expired_count
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_recommendation_expiry_jobs() -> None:
    scheduler.add_job(
        expire_recommendations,
        "interval",
        hours=1,
        id="expire_stale_recommendations",
        replace_existing=True,
    )
