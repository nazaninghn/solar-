import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analytics.router import router as analytics_router
from app.core.config import settings
from app.core.error_tracking import configure_error_tracking
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware
from app.database.session import get_db
from app.jobs.device_jobs import run_device_polling_loop
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.modules.auth.router import router as auth_router
from app.modules.battery.router import router as battery_router
from app.modules.company.router import router as company_router
from app.modules.devices.router import device_router, router as devices_router
from app.modules.energy.router import router as energy_router
from app.modules.factories.router import router as factories_router
from app.modules.financial.router import router as financial_router
from app.modules.forecast.router import router as forecast_router
from app.modules.notifications.router import notification_router, router as notifications_router
from app.modules.pricing.router import router as pricing_router
from app.modules.production_lines.router import router as production_lines_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.system.router import router as system_router
from app.modules.weather.router import router as weather_router
from app.modules.control.router import router as control_router
from app.modules.gateway.router import router as gateway_router
from app.modules.pipeline.router import router as pipeline_router
from app.modules.forecasting.router import router as forecasting_router
from app.modules.optimization.router import router as optimization_router
from app.modules.finance.router import router as finance_router
from app.modules.orchestrator.router import router as orchestrator_router
from app.modules.iot_gateway.router import router as iot_gateway_router
from app.realtime.router import router as realtime_router

configure_logging()
configure_error_tracking()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    device_polling_task = asyncio.create_task(run_device_polling_loop())
    yield
    device_polling_task.cancel()
    stop_scheduler()


app = FastAPI(
    title="SolarFlow API",
    description="Industrial Solar Energy Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# 27.17: origins come only from CORS_ALLOWED_ORIGINS — no "*" fallback.
# An empty list (unset env var) means no cross-origin browser requests
# succeed, which is the correct failure mode for a misconfigured
# production deploy, not silently allowing everything.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# 28.6-28.8: added after CORS so it's the outermost layer — timing and
# the request_id cover the full request lifecycle, including CORS
# preflight handling.
app.add_middleware(RequestLoggingMiddleware)

app.include_router(auth_router)
app.include_router(company_router)
app.include_router(factories_router)
app.include_router(energy_router)
app.include_router(weather_router)
app.include_router(forecast_router)
app.include_router(battery_router)
app.include_router(pricing_router)
app.include_router(recommendations_router)
app.include_router(financial_router)
app.include_router(notifications_router)
app.include_router(notification_router)
app.include_router(realtime_router)
app.include_router(devices_router)
app.include_router(device_router)
app.include_router(production_lines_router)
app.include_router(analytics_router)
app.include_router(system_router)
app.include_router(control_router)
app.include_router(gateway_router)
app.include_router(pipeline_router)
app.include_router(forecasting_router)
app.include_router(optimization_router)
app.include_router(finance_router)
app.include_router(orchestrator_router)
app.include_router(iot_gateway_router)


@app.get("/")
def root():
    return {
        "name": "SolarFlow API",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    """
    27.13-27.14: pure liveness — no dependencies checked. This is what
    Render's own health check should point at, since a momentary DB
    blip shouldn't make Render think the whole process is dead and
    recycle it. Dependency checks live at /health/ready instead.
    """
    return {"status": "ok"}


@app.get("/health/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        database_status = "error"

    overall_status = "ready" if database_status == "ok" else "not_ready"

    return {
        "status": overall_status,
        "database": database_status,
    }
