"""
STEP 41.17-41.21: System Health Checks.

Checks database, queue, MQTT, weather/price feeds, forecast engine.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.observability.models import DataSource, SRC_DEGRADED, SRC_DOWN, SRC_HEALTHY, SRC_UNKNOWN

logger = logging.getLogger(__name__)


def check_database_health(db: Session) -> str:
    """41.21: Database connectivity check."""
    try:
        db.execute(text("SELECT 1"))
        return "HEALTHY"
    except Exception:
        return "DOWN"


def check_source_health(db: Session, source_name: str) -> str:
    """Check a specific data source health."""
    source = db.query(DataSource).filter(DataSource.name == source_name).first()
    if not source:
        return SRC_UNKNOWN

    return source.status


def get_system_health(db: Session) -> dict:
    """41.18: Aggregate system health status."""
    db_status = check_database_health(db)

    # Check data sources
    sources = db.query(DataSource).all()
    source_map = {s.name: s.status for s in sources}

    weather = source_map.get("weather_api", SRC_UNKNOWN)
    price = source_map.get("price_feed", SRC_UNKNOWN)
    forecast = source_map.get("forecast_engine", SRC_UNKNOWN)
    mqtt = source_map.get("mqtt_broker", SRC_UNKNOWN)
    queue = source_map.get("job_queue", SRC_UNKNOWN)

    # Overall: worst of critical components
    statuses = [db_status, weather, price, forecast]
    if "DOWN" in statuses:
        overall = "DOWN"
    elif "DEGRADED" in statuses or SRC_UNKNOWN in statuses:
        overall = "DEGRADED"
    else:
        overall = "HEALTHY"

    return {
        "api": "HEALTHY",  # If we're responding, API is up
        "database": db_status,
        "queue": queue,
        "mqtt": mqtt,
        "weather_feed": weather,
        "price_feed": price,
        "forecast": forecast,
        "overall": overall,
    }


def update_source_health(
    db: Session,
    source_name: str,
    success: bool,
    latency_ms: int | None = None,
    error_message: str | None = None,
) -> DataSource:
    """Update a data source health after a fetch attempt."""
    now = datetime.now(timezone.utc)

    source = db.query(DataSource).filter(DataSource.name == source_name).first()
    if not source:
        source = DataSource(
            type="external",
            name=source_name,
            status=SRC_UNKNOWN,
            created_at=now,
        )
        db.add(source)

    if success:
        source.status = SRC_HEALTHY
        source.last_success_at = now
        source.consecutive_failures = 0
        source.latency_ms = latency_ms
        source.last_error_message = None
    else:
        source.consecutive_failures += 1
        source.last_error_at = now
        source.last_error_message = error_message
        if source.consecutive_failures >= 3:
            source.status = SRC_DOWN
        else:
            source.status = SRC_DEGRADED

    source.updated_at = now
    db.commit()
    db.refresh(source)
    return source
