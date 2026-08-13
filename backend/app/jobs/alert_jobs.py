from app.database.session import SessionLocal
from app.jobs.common import finish_job_run, get_all_factories, start_job_run
from app.jobs.scheduler import scheduler
from app.modules.notifications.engine import evaluate_all_alert_rules
from app.modules.recommendations.service import build_energy_context

JOB_NAME = "run_alert_engine"


async def run_alert_engine() -> None:
    """
    25.20: alerts previously only fired as a side effect of the hourly
    recommendation job (Step 23) — fine for most categories, but battery-
    critical/price-spike/system-health are exactly the kind of thing that
    shouldn't wait up to an hour. This runs the same rule set on its own
    5-minute cadence; Step 23's cooldown-based dedup in create_notification
    already prevents this from duplicating the hourly job's alerts.

    Note: build_energy_context calls get_factory_forecast, which hits the
    live weather API (degrades gracefully to 0/0 on failure, per Step 20).
    Running that every 5 minutes instead of hourly is a real increase in
    external API calls — acceptable for now on the free Open-Meteo tier,
    but worth revisiting (e.g. reading the already-persisted SolarForecast
    table instead) if that ever becomes a rate-limit concern.
    """
    db = SessionLocal()
    job_run = start_job_run(db, JOB_NAME)

    try:
        factories = get_all_factories(db)

        for factory in factories:
            context = await build_energy_context(db, factory)
            evaluate_all_alert_rules(db, factory, context)

        finish_job_run(db, job_run, status="success")
    except Exception as error:
        finish_job_run(db, job_run, status="failed", error_message=str(error))
        raise
    finally:
        db.close()


def register_alert_jobs() -> None:
    scheduler.add_job(
        run_alert_engine,
        "interval",
        minutes=5,
        id="run_alert_engine",
        replace_existing=True,
    )
