from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.forecast.solar import calculate_forecast_confidence, calculate_solar_power
from app.models.energy_reading import EnergyReading
from app.models.factory import Factory
from app.models.solar_forecast import SolarForecast
from app.weather.providers.open_meteo_provider import OpenMeteoProvider
from app.weather.service import WeatherService


async def generate_and_store_solar_forecast(
    db: Session,
    factory: Factory,
    days: int = 7,
) -> list[SolarForecast]:
    """
    19.35's scheduler flow: fetch weather, run each hourly point through
    the physical solar model, upsert by (factory_id, timestamp) so
    re-running doesn't duplicate — same idempotency pattern as every
    other scheduled job in this project.
    """
    weather_service = WeatherService(OpenMeteoProvider())
    weather_points = await weather_service.get_forecast(
        latitude=factory.latitude,
        longitude=factory.longitude,
        days=days,
    )

    capacity_kwp = factory.solar_capacity_kw or 0.0
    now = datetime.now(timezone.utc)

    # Deliberately not filtered to `timestamp >= now` — Open-Meteo
    # returns hourly points starting from today's midnight, which is
    # already in the past relative to "now" partway through the day.
    # Filtering here missed those earlier rows on a second run of the
    # same day and tried to re-insert them, hitting the unique
    # constraint instead of updating in place.
    incoming_timestamps = [point.timestamp for point in weather_points]

    existing_by_timestamp = {
        row.timestamp: row
        for row in db.scalars(
            select(SolarForecast).where(
                SolarForecast.factory_id == factory.id,
                SolarForecast.timestamp.in_(incoming_timestamps),
            )
        ).all()
    }

    rows = []

    for point in weather_points:
        irradiance = point.solar_irradiance_w_m2 or 0.0

        expected_power_kw = calculate_solar_power(
            capacity_kwp=capacity_kwp,
            irradiance_w_m2=irradiance,
        )
        confidence = calculate_forecast_confidence(point.cloud_cover_percent)

        existing = existing_by_timestamp.get(point.timestamp)

        if existing:
            row = existing
        else:
            row = SolarForecast(factory_id=factory.id, timestamp=point.timestamp)
            db.add(row)

        row.expected_power_kw = round(expected_power_kw, 2)
        row.expected_energy_kwh = round(expected_power_kw, 2)  # 1-hour resolution
        row.confidence = confidence
        row.is_stale = False
        row.created_at = now

        rows.append(row)

    db.commit()

    return rows


def get_stored_solar_forecast(
    db: Session,
    factory_id: int,
    start: datetime,
    end: datetime,
) -> list[SolarForecast]:
    return db.scalars(
        select(SolarForecast)
        .where(
            SolarForecast.factory_id == factory_id,
            SolarForecast.timestamp >= start,
            SolarForecast.timestamp <= end,
        )
        .order_by(SolarForecast.timestamp.asc())
    ).all()


async def get_solar_forecast(
    db: Session,
    factory: Factory,
) -> tuple[list[SolarForecast], bool]:
    """
    19.36: try to generate a fresh forecast; if the weather API call
    fails, fall back to whatever was last persisted for this factory
    and report it as stale rather than raising — a Dashboard shouldn't
    go blank because a weather provider timed out.
    """
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=7)

    if factory.latitude is None or factory.longitude is None:
        return [], True

    try:
        await generate_and_store_solar_forecast(db, factory)
        return get_stored_solar_forecast(db, factory.id, now, end), False
    except Exception:
        stale_rows = get_stored_solar_forecast(db, factory.id, now, end)

        for row in stale_rows:
            row.is_stale = True

        db.commit()

        return stale_rows, True


def _get_hourly_consumption_profile(
    db: Session,
    factory_id: int,
    days: int = 30,
) -> dict[int, float]:
    """
    Average consumption_kwh by hour-of-day from historical EnergyReading
    rows — needed to turn a solar forecast into an energy (deficit vs.
    surplus) forecast, since nothing in Step 19's brief defines a
    consumption forecast model.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    rows = db.execute(
        select(
            func.extract("hour", EnergyReading.timestamp).label("hour"),
            func.avg(EnergyReading.consumption_kwh).label("avg_consumption"),
        )
        .where(
            EnergyReading.factory_id == factory_id,
            EnergyReading.timestamp >= cutoff,
        )
        .group_by(func.extract("hour", EnergyReading.timestamp))
    ).all()

    return {int(row.hour): row.avg_consumption for row in rows}


async def get_energy_forecast(
    db: Session,
    factory: Factory,
) -> tuple[list[dict], bool]:
    solar_rows, is_stale = await get_solar_forecast(db, factory)

    profile = _get_hourly_consumption_profile(db, factory.id)
    overall_avg = sum(profile.values()) / len(profile) if profile else 0.0

    forecast = []

    for row in solar_rows:
        expected_consumption_kwh = profile.get(row.timestamp.hour, overall_avg)

        forecast.append(
            {
                "timestamp": row.timestamp,
                "expected_solar_kwh": row.expected_energy_kwh,
                "expected_consumption_kwh": round(expected_consumption_kwh, 2),
                "expected_balance_kwh": round(
                    row.expected_energy_kwh - expected_consumption_kwh, 2
                ),
            }
        )

    return forecast, is_stale
