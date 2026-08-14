import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.ai_readiness.drift_detection import detect_forecast_drift
from app.modules.ai_readiness.model_governance import seed_model_registry
from app.modules.monitoring.models import MonitoringIncident

logger = logging.getLogger(__name__)


def refresh_model_registry_and_check_drift() -> None:
    """81: Model Monitoring — refreshes ForecastModelRegistry against
    the latest ForecastAccuracy history, then checks for drift.
    Same MonitoringIncident-reuse + dedup pattern as Steps 78-80's
    alert jobs."""
    db = SessionLocal()
    job_run = start_job_run(db, "refresh_model_registry_and_check_drift")

    try:
        seeded = seed_model_registry(db)
        logger.info("refreshed %d model registry entries", len(seeded))

        drift_results = detect_forecast_drift(db)
        opened = 0

        for entry in drift_results:
            if not entry["drifted"]:
                continue

            dedup_key = f"FORECAST_DRIFT:{entry['forecast_type']}"
            already_open = (
                db.scalar(
                    select(MonitoringIncident.id).where(
                        MonitoringIncident.service == "ai_readiness",
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
                    title=f"Forecast accuracy drift: {entry['forecast_type']} ({dedup_key})",
                    severity="WARNING",
                    status="OPEN",
                    service="ai_readiness",
                    started_at=now,
                    root_cause=(
                        f"MAE degraded {entry['drift_percent']}% "
                        f"({entry['prior_mae']} -> {entry['recent_mae']}) over the last "
                        f"14 days vs the prior 14"
                    ),
                    created_at=now,
                )
            )
            opened += 1

        db.commit()
        if opened:
            logger.warning("opened %d forecast drift incident(s)", opened)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_ai_readiness_jobs() -> None:
    scheduler.add_job(
        refresh_model_registry_and_check_drift,
        "cron",
        hour=5,
        minute=0,
        id="refresh_model_registry_and_check_drift",
        replace_existing=True,
    )
