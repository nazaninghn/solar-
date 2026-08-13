from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_run import JobRun


def get_latest_job_statuses(db: Session) -> list[JobRun]:
    """One row per distinct job_name: its most recent run."""
    return db.scalars(
        select(JobRun)
        .distinct(JobRun.job_name)
        .order_by(JobRun.job_name, JobRun.started_at.desc())
    ).all()
