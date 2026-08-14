import logging
from datetime import timedelta

from app.analytics.service import get_today_analytics
from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, get_all_factories, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.notifications.service import create_notification

logger = logging.getLogger(__name__)

JOB_NAME = "generate_daily_summary"

# 30.15: rule_id + a cooldown just under 24h gives "once per calendar
# day" for free via the existing cooldown-dedup mechanism
# (23.18-23.19) — no separate "last summary date" tracking needed. A
# manual re-run later the same day won't duplicate; tomorrow's 23:00
# run will, since by then the cooldown window has passed.
_SUMMARY_COOLDOWN_MINUTES = int(timedelta(hours=20).total_seconds() / 60)


def generate_daily_summary() -> None:
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        factories = get_all_factories(db)
        generated = 0

        for factory in factories:
            summary = get_today_analytics(db, factory.id)

            if summary is None:
                continue

            message_parts = [
                f"Solar: {summary['solar_generation_kwh']:.0f} kWh",
                f"Consumption: {summary['factory_consumption_kwh']:.0f} kWh",
                f"Grid import: {summary['grid_import_kwh']:.0f} kWh",
                f"Solar coverage: {summary['solar_coverage_percent']:.0f}%",
            ]

            if summary.get("grid_cost_today") is not None:
                message_parts.append(f"Grid cost: {summary['grid_cost_today']:.0f}")
            if summary.get("battery_soc") is not None:
                message_parts.append(f"Battery: {summary['battery_soc']:.0f}%")

            create_notification(
                db=db,
                factory_id=factory.id,
                notification_type="ENERGY",
                severity="INFO",
                title="Daily Energy Summary",
                message=" | ".join(message_parts),
                rule_id="DAILY_SUMMARY",
                cooldown_minutes=_SUMMARY_COOLDOWN_MINUTES,
                source="DAILY_SUMMARY",
                alert_metadata={
                    "related_resource": "analytics",
                    "deep_link": "/analytics",
                    "solar_generation_kwh": summary["solar_generation_kwh"],
                    "factory_consumption_kwh": summary["factory_consumption_kwh"],
                    "grid_import_kwh": summary["grid_import_kwh"],
                    "grid_export_kwh": summary["grid_export_kwh"],
                    "solar_coverage_percent": summary["solar_coverage_percent"],
                    "grid_cost_today": summary.get("grid_cost_today"),
                    "battery_soc": summary.get("battery_soc"),
                },
            )
            generated += 1

        logger.info("generated %d daily summaries", generated)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_daily_summary_jobs() -> None:
    scheduler.add_job(
        generate_daily_summary,
        "cron",
        hour=23,
        minute=0,
        id="generate_daily_summary",
        replace_existing=True,
    )
