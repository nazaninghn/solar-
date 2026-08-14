import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.models.device_energy_reading import DeviceEnergyReading
from app.models.factory import Factory
from app.modules.compliance.service import get_held_organization_ids
from app.modules.observability.models import DataQualityEvent, SystemMetricSnapshot

logger = logging.getLogger(__name__)

JOB_NAME = "purge_old_telemetry"

# 26.27: "مقادیر دقیق را بعداً بر اساس هزینه Database تعیین می‌کنیم" —
# a provisional default, tunable later. Scoped to DeviceEnergyReading
# only (the per-device raw table growing at polling-cadence rates,
# 26.17's "52 million+ rows/year" concern) — EnergyReading/Hourly/Daily/
# Monthly are already coarser aggregates meant to be kept for years and
# are orders of magnitude lower volume.
RAW_TELEMETRY_RETENTION_DAYS = 90

# 77.70: SystemMetricSnapshot is written every 5 minutes (app.jobs.
# observability_jobs) — ~300 rows/day, genuinely unbounded growth with
# no long-term value past a month of trend data. DataQualityEvent is
# lower-frequency but still an event log, not a compliance record.
#
# Deliberately NOT extended to AuditLog, AdminAuditLog, SecurityEvent,
# RecommendationAuditLog, or the incident/postmortem tables — those are
# audit trails a company may have a compliance reason to keep
# indefinitely, and picking a retention window for someone else's audit
# obligation isn't a call this job should make unilaterally.
SYSTEM_METRIC_SNAPSHOT_RETENTION_DAYS = 30
DATA_QUALITY_EVENT_RETENTION_DAYS = 180


def _held_factory_ids(db) -> set[int]:
    """79.33: a factory belonging to an organization under legal hold
    is excluded from every purge below — its data must survive past
    its normal retention window until the hold is released."""
    held_org_ids = get_held_organization_ids(db)
    if not held_org_ids:
        return set()

    return set(
        db.scalars(select(Factory.id).where(Factory.organization_id.in_(held_org_ids))).all()
    )


def purge_old_telemetry() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=RAW_TELEMETRY_RETENTION_DAYS)
        held_factory_ids = _held_factory_ids(db)

        query = delete(DeviceEnergyReading).where(DeviceEnergyReading.timestamp < cutoff)
        if held_factory_ids:
            query = query.where(DeviceEnergyReading.factory_id.notin_(held_factory_ids))

        result = db.execute(query)
        deleted_count = result.rowcount

        db.commit()

        logger.info(
            "purged %d device_energy_readings rows older than %s",
            deleted_count,
            cutoff.isoformat(),
        )

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def purge_old_observability_data() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, "purge_old_observability_data")

    try:
        metric_cutoff = datetime.now(timezone.utc) - timedelta(
            days=SYSTEM_METRIC_SNAPSHOT_RETENTION_DAYS
        )
        quality_event_cutoff = datetime.now(timezone.utc) - timedelta(
            days=DATA_QUALITY_EVENT_RETENTION_DAYS
        )
        held_factory_ids = _held_factory_ids(db)

        # SystemMetricSnapshot has no factory dimension (platform-wide
        # metrics, not customer data) — nothing to hold there.
        metrics_deleted = db.execute(
            delete(SystemMetricSnapshot).where(SystemMetricSnapshot.timestamp < metric_cutoff)
        ).rowcount

        quality_event_query = delete(DataQualityEvent).where(
            DataQualityEvent.started_at < quality_event_cutoff
        )
        if held_factory_ids:
            quality_event_query = quality_event_query.where(
                DataQualityEvent.factory_id.notin_(held_factory_ids)
            )
        events_deleted = db.execute(quality_event_query).rowcount

        db.commit()

        logger.info(
            "purged %d system_metric_snapshots and %d data_quality_events rows",
            metrics_deleted,
            events_deleted,
        )

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_retention_jobs() -> None:
    scheduler.add_job(
        purge_old_telemetry,
        "cron",
        hour=2,
        minute=30,
        id="purge_old_telemetry",
        replace_existing=True,
    )
    scheduler.add_job(
        purge_old_observability_data,
        "cron",
        hour=2,
        minute=45,
        id="purge_old_observability_data",
        replace_existing=True,
    )
