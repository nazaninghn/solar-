from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.external_api_metrics import get_external_api_snapshot
from app.core.metrics import get_request_metrics_snapshot
from app.database.session import engine
from app.jobs.scheduler import scheduler
from app.models.device import Device
from app.models.job_run import JobRun


def get_latest_job_statuses(db: Session) -> list[JobRun]:
    """One row per distinct job_name: its most recent run."""
    return db.scalars(
        select(JobRun)
        .distinct(JobRun.job_name)
        .order_by(JobRun.job_name, JobRun.started_at.desc())
    ).all()


def get_device_status_counts(db: Session) -> dict:
    """
    28.19, 28.34: ONLINE / WARNING / OFFLINE — the model's actual status
    values are ONLINE/OFFLINE/ERROR/UNKNOWN (16.13-16.14); ERROR and
    UNKNOWN both fold into "warning" here since neither means "confirmed
    down" the way OFFLINE (the device_health_jobs.py threshold check)
    does — a device stuck on ERROR is degraded, not necessarily offline.
    """
    rows = db.execute(
        select(Device.status, func.count())
        .where(Device.is_active.is_(True))
        .group_by(Device.status)
    ).all()

    counts = {"online": 0, "warning": 0, "offline": 0}

    for status_value, count in rows:
        if status_value == "ONLINE":
            counts["online"] += count
        elif status_value == "OFFLINE":
            counts["offline"] += count
        else:
            counts["warning"] += count

    counts["total"] = counts["online"] + counts["warning"] + counts["offline"]

    return counts


def get_database_pool_stats() -> dict:
    """28.14: connection pool usage, not query-level detail — that's
    db_monitoring.py's slow-query logging instead."""
    pool = engine.pool

    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "checked_in": pool.checkedin(),
        "overflow": pool.overflow(),
    }


def get_system_health_summary(db: Session) -> dict:
    """
    28.31-28.36: one call a future admin dashboard page would make to
    render the whole "System Status" view — API/DB/scheduler/device/
    external-API cards. Backend data only; no frontend page exists in
    this repo (the frontend is the separate Next.js project on Vercel).
    """
    # Database
    try:
        db.execute(text("SELECT 1"))
        database_status = "healthy"
    except Exception:
        database_status = "unhealthy"

    # Scheduler / jobs — "healthy" only if the in-process APScheduler is
    # actually running AND the most recent run of every job succeeded.
    job_runs = get_latest_job_statuses(db)
    failed_jobs = [j.job_name for j in job_runs if j.status == "failed"]

    if not scheduler.running:
        scheduler_status = "unhealthy"
    elif failed_jobs:
        scheduler_status = "degraded"
    else:
        scheduler_status = "healthy"

    # Devices
    device_counts = get_device_status_counts(db)

    if device_counts["total"] == 0:
        device_status = "healthy"
    elif device_counts["offline"] > 0:
        device_status = "degraded" if device_counts["offline"] < device_counts["total"] else "unhealthy"
    elif device_counts["warning"] > 0:
        device_status = "degraded"
    else:
        device_status = "healthy"

    # External APIs
    external_apis = get_external_api_snapshot()
    external_api_statuses = [stats["status"] for stats in external_apis.values()]

    if any(s == "unhealthy" for s in external_api_statuses):
        external_api_status = "unhealthy"
    elif any(s == "degraded" for s in external_api_statuses):
        external_api_status = "degraded"
    else:
        external_api_status = "healthy"

    # API (this process itself, answering the request) — request error
    # rate is the signal, since "the process is up" is already implied
    # by this code running at all.
    request_metrics = get_request_metrics_snapshot()
    api_status = "unhealthy" if request_metrics["error_rate_percent"] > 5 else "healthy"

    component_statuses = [
        database_status,
        scheduler_status,
        device_status,
        external_api_status,
        api_status,
    ]

    if "unhealthy" in component_statuses:
        overall_status = "unhealthy"
    elif "degraded" in component_statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "overall_status": overall_status,
        "api": {
            "status": api_status,
            "average_latency_ms": request_metrics["average_duration_ms"],
            "error_rate_percent": request_metrics["error_rate_percent"],
        },
        "database": {"status": database_status},
        "scheduler": {
            "status": scheduler_status,
            "jobs_total": len(job_runs),
            "jobs_failed": len(failed_jobs),
            "failed_job_names": failed_jobs,
        },
        "devices": {"status": device_status, **device_counts},
        "external_apis": {"status": external_api_status, "providers": external_apis},
    }
