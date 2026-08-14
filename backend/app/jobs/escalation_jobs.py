import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.auth.access_control import list_users_with_factory_access
from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, start_job_run
from app.jobs.scheduler import scheduler
from app.models.factory import Factory
from app.models.notification import Notification
from app.modules.alerts.oncall import get_current_on_call
from app.modules.notifications.service import create_notification

logger = logging.getLogger(__name__)

JOB_NAME = "escalate_unacknowledged_critical_alerts"

# 30.13: provisional, tunable later — how long a CRITICAL alert can sit
# unacknowledged before someone else gets pinged about it.
ESCALATION_THRESHOLD_MINUTES = 15
ESCALATION_ROLES = ("FACTORY_MANAGER", "ENERGY_MANAGER")


def escalate_unacknowledged_critical_alerts() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=ESCALATION_THRESHOLD_MINUTES
        )

        unacknowledged = db.scalars(
            select(Notification).where(
                Notification.severity == "CRITICAL",
                Notification.status.notin_(["RESOLVED", "DISMISSED"]),
                Notification.acknowledged_at.is_(None),
                Notification.escalated_at.is_(None),
                Notification.created_at < cutoff,
            )
        ).all()

        for notification in unacknowledged:
            _escalate(db, notification)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def _escalate(db, notification: Notification) -> None:
    factory = db.get(Factory, notification.factory_id)

    if factory is None:
        return

    users_with_access = list_users_with_factory_access(db, factory)
    candidates = [u for u in users_with_access if u.role in ESCALATION_ROLES]

    # Escalation should always reach *someone* — fall back to company
    # admins rather than silently doing nothing if this factory has no
    # FACTORY_MANAGER/ENERGY_MANAGER assigned.
    if not candidates:
        candidates = [
            u for u in users_with_access if u.role in ("COMPANY_ADMIN", "SUPER_ADMIN")
        ]

    # 77.61-77.63: whoever's on the current on-call shift gets notified
    # too, in addition to (not instead of) the role-based candidates
    # above — an on-call schedule doesn't replace the role fallback,
    # since a factory with no schedule configured shouldn't lose
    # escalation coverage entirely.
    on_call_user = get_current_on_call(db, factory.id)
    if on_call_user and on_call_user not in candidates:
        candidates.append(on_call_user)

    for user in candidates:
        create_notification(
            db=db,
            factory_id=factory.id,
            user_id=user.id,
            notification_type=notification.type,
            severity="CRITICAL",
            title=f"ESCALATED: {notification.title}",
            message=(
                f"Unacknowledged for over {ESCALATION_THRESHOLD_MINUTES} minutes: "
                f"{notification.message}"
            ),
            source="ESCALATION",
            alert_metadata={
                "related_resource": "escalation",
                "escalated_notification_id": notification.id,
            },
        )

    notification.escalated_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "escalated notification %d to %d recipient(s)",
        notification.id,
        len(candidates),
    )


def register_escalation_jobs() -> None:
    scheduler.add_job(
        escalate_unacknowledged_critical_alerts,
        "interval",
        minutes=5,
        id="escalate_unacknowledged_critical_alerts",
        replace_existing=True,
    )
