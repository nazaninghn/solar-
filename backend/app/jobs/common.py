"""
Not in the brief's file list (13.2), but every job needs both of these:
a plain, un-scoped factory query (jobs are system-level, not
request-scoped, so app.core.dependencies.get_accessible_factory doesn't
apply here) and a consistent way to record JobRun rows (13.19-13.22)
without repeating the same start/finish boilerplate five times.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.factory import Factory
from app.models.job_run import JobRun


def get_all_factories(db: Session) -> list[Factory]:
    """
    Factory has no is_active/status column yet, so "active factories"
    (13.10) currently just means "all factories". If a deactivation
    concept gets added later, this is the one place to filter it.
    """
    return db.scalars(select(Factory)).all()


def start_job_run(db: Session, job_name: str) -> JobRun:
    job_run = JobRun(
        job_name=job_name,
        status="running",
        started_at=datetime.now(timezone.utc),
    )

    db.add(job_run)
    db.commit()
    db.refresh(job_run)

    return job_run


def finish_job_run(
    db: Session,
    job_run: JobRun,
    status: str,
    error_message: str | None = None,
) -> None:
    job_run.status = status
    job_run.finished_at = datetime.now(timezone.utc)
    job_run.error_message = error_message
    job_run.duration_ms = int(
        (job_run.finished_at - job_run.started_at).total_seconds() * 1000
    )

    db.commit()
