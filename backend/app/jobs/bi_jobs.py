import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.bi.alerts import check_kpi_alerts
from app.modules.monitoring.models import MonitoringIncident

logger = logging.getLogger(__name__)


def check_bi_kpi_alerts() -> None:
    """80: KPI Alerts — same MonitoringIncident-reuse + dedup pattern
    as app.jobs.finops_jobs.check_budget_alerts and app.modules.
    security.correlation."""
    db = SessionLocal()
    job_run = start_job_run(db, "check_bi_kpi_alerts")

    try:
        breaches = check_kpi_alerts(db)
        opened = 0

        for breach in breaches:
            dedup_key = breach["key"]
            already_open = (
                db.scalar(
                    select(MonitoringIncident.id).where(
                        MonitoringIncident.service == "bi",
                        MonitoringIncident.title.like(f"%{dedup_key}%"),
                        MonitoringIncident.status.in_(["OPEN", "ACKNOWLEDGED", "INVESTIGATING"]),
                    )
                )
                is not None
            )
            if already_open:
                continue

            now = datetime.now(timezone.utc)
            db.add(
                MonitoringIncident(
                    title=f"KPI alert: {dedup_key}",
                    severity=breach["severity"],
                    status="OPEN",
                    service="bi",
                    started_at=now,
                    root_cause=breach["detail"],
                    created_at=now,
                )
            )
            opened += 1

        db.commit()
        if opened:
            logger.warning("opened %d KPI alert incident(s)", opened)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_bi_jobs() -> None:
    scheduler.add_job(
        check_bi_kpi_alerts,
        "cron",
        hour=6,
        minute=0,
        id="check_bi_kpi_alerts",
        replace_existing=True,
    )
