"""
In-process job scheduling via APScheduler, running inside the same
FastAPI process as the web server (wired into app/main.py's lifespan) —
no Redis, no Celery, no separate worker/beat process. This was an
explicit choice (Step 25): the existing scheduler already covered 8 of
10 job types, had idempotent upserts everywhere, and a single-process
deploy is simpler and cheaper on Render than provisioning Redis plus
two extra services for a project at this scale. If a genuine need for
distributed workers or true task retries across multiple instances
shows up later, that's the point to revisit this decision — not before.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()


def register_all_jobs() -> None:
    # Deferred imports: each job module does `from app.jobs.scheduler
    # import scheduler` at its own top level, so importing them here
    # (inside the function, called at runtime) avoids relying on Python's
    # partial-module circular-import behavior that the brief's top-level
    # version (13.6-13.7) would otherwise depend on.
    from app.jobs.aggregation_jobs import register_aggregation_jobs
    from app.jobs.ai_readiness_jobs import register_ai_readiness_jobs
    from app.jobs.alert_jobs import register_alert_jobs
    from app.jobs.bi_jobs import register_bi_jobs
    from app.jobs.daily_summary_jobs import register_daily_summary_jobs
    from app.jobs.device_health_jobs import register_device_health_jobs
    from app.jobs.disaster_recovery_jobs import register_disaster_recovery_jobs
    from app.jobs.escalation_jobs import register_escalation_jobs
    from app.jobs.financial_jobs import register_financial_jobs
    from app.jobs.finops_jobs import register_finops_jobs
    from app.jobs.observability_jobs import register_observability_jobs
    from app.jobs.performance_jobs import register_performance_jobs
    from app.jobs.pricing_jobs import register_pricing_jobs
    from app.jobs.recommendation_expiry_jobs import register_recommendation_expiry_jobs
    from app.jobs.recommendation_jobs import register_recommendation_jobs
    from app.jobs.retention_jobs import register_retention_jobs
    from app.jobs.security_jobs import register_security_jobs
    from app.jobs.solar_forecast_jobs import register_solar_forecast_jobs

    # Step 25: weather_jobs.update_weather and forecast_jobs.update_solar_
    # forecast were retired — both fetched from the external weather API
    # and discarded the result (no caching layer exists anywhere in this
    # request path), so they burned API quota on a fixed interval for
    # zero benefit to any consumer. generate_solar_forecasts below is the
    # one job that actually persists what it fetches.
    register_pricing_jobs()
    register_recommendation_jobs()
    register_financial_jobs()
    register_aggregation_jobs()
    register_solar_forecast_jobs()
    register_recommendation_expiry_jobs()
    register_alert_jobs()
    register_device_health_jobs()
    register_retention_jobs()
    register_escalation_jobs()
    register_daily_summary_jobs()
    register_observability_jobs()
    register_security_jobs()
    register_finops_jobs()
    register_bi_jobs()
    register_ai_readiness_jobs()
    register_disaster_recovery_jobs()
    register_performance_jobs()


def start_scheduler() -> None:
    register_all_jobs()

    if not scheduler.running:
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
