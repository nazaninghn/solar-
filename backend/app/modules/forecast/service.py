from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.integrations.weather.service import WeatherService
from app.models.energy_reading import EnergyReading
from app.models.factory import Factory


def calculate_weather_factor(cloud_coverage: float) -> float:
    if cloud_coverage <= 10:
        return 1.0

    if cloud_coverage <= 30:
        return 0.9

    if cloud_coverage <= 50:
        return 0.78

    if cloud_coverage <= 70:
        return 0.60

    if cloud_coverage <= 90:
        return 0.40

    return 0.25


def calculate_solar_forecast(
    historical_baseline_kwh: float,
    cloud_coverage: float,
) -> dict:
    weather_factor = calculate_weather_factor(cloud_coverage)
    forecast = historical_baseline_kwh * weather_factor

    return {
        "baseline_kwh": round(historical_baseline_kwh, 2),
        "weather_factor": weather_factor,
        "forecast_kwh": round(forecast, 2),
    }


def describe_cloud_coverage(cloud_coverage: float) -> str:
    """
    Human-readable label for the same buckets used by
    calculate_weather_factor, since the brief's forecast response shape
    (8.26) includes a "condition" string that Open-Meteo's raw hourly
    payload doesn't provide directly.
    """
    if cloud_coverage <= 10:
        return "Clear"

    if cloud_coverage <= 30:
        return "Mostly Clear"

    if cloud_coverage <= 50:
        return "Partly Cloudy"

    if cloud_coverage <= 70:
        return "Cloudy"

    if cloud_coverage <= 90:
        return "Very Cloudy"

    return "Overcast"


def extract_tomorrow_cloud_coverage(weather_data: dict) -> float:
    """
    Averages Open-Meteo's hourly cloud_cover values that fall on
    tomorrow's UTC date. Needed because the brief's calculate_solar_forecast
    takes a single cloud_coverage number, but the provider returns an
    hourly series.
    """
    hourly = weather_data.get("hourly", {})
    times = hourly.get("time", [])
    clouds = hourly.get("cloud_cover", [])

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()

    values = [
        cloud
        for time_str, cloud in zip(times, clouds)
        if time_str.startswith(tomorrow)
    ]

    if not values:
        return 0.0

    return sum(values) / len(values)


def get_historical_baseline_kwh(
    db: Session,
    factory_id: int,
    days: int = 30,
) -> float:
    """
    Average daily solar production over the trailing window, computed
    from real EnergyReading rows rather than a hardcoded number, since
    the brief's "Historical Production" input has to come from somewhere.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    daily_sums = db.execute(
        select(
            func.date(EnergyReading.timestamp).label("day"),
            func.sum(EnergyReading.solar_generation_kwh).label("total"),
        )
        .where(
            EnergyReading.factory_id == factory_id,
            EnergyReading.timestamp >= cutoff,
        )
        .group_by(func.date(EnergyReading.timestamp))
    ).all()

    if not daily_sums:
        return 0.0

    return sum(row.total for row in daily_sums) / len(daily_sums)


def count_historical_days(
    db: Session,
    factory_id: int,
    days: int = 30,
) -> int:
    """
    How many distinct days of EnergyReading history exist in the trailing
    window. Used as a data-quality signal for the battery recommendation's
    confidence score (Step 9) — a baseline built from 1 day of data is
    far less trustworthy than one built from 30.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    daily_sums = db.execute(
        select(func.date(EnergyReading.timestamp).label("day"))
        .where(
            EnergyReading.factory_id == factory_id,
            EnergyReading.timestamp >= cutoff,
        )
        .group_by(func.date(EnergyReading.timestamp))
    ).all()

    return len(daily_sums)


async def get_factory_forecast(db: Session, factory: Factory) -> dict:
    if factory.latitude is None or factory.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Factory location is not configured",
        )

    weather_service = WeatherService()
    weather_data = await weather_service.get_factory_forecast(
        latitude=factory.latitude,
        longitude=factory.longitude,
    )

    cloud_coverage = extract_tomorrow_cloud_coverage(weather_data)
    baseline_kwh = get_historical_baseline_kwh(db, factory.id)

    forecast = calculate_solar_forecast(baseline_kwh, cloud_coverage)

    reduction_percent = 0.0
    if forecast["baseline_kwh"] > 0:
        reduction_percent = round(
            (1 - forecast["forecast_kwh"] / forecast["baseline_kwh"]) * 100, 2
        )

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).date()

    return {
        "factory_id": factory.id,
        "forecast_date": tomorrow,
        "weather": {
            "condition": describe_cloud_coverage(cloud_coverage),
            "cloud_coverage": round(cloud_coverage, 1),
        },
        "solar": {
            "baseline_kwh": forecast["baseline_kwh"],
            "forecast_kwh": forecast["forecast_kwh"],
            "reduction_percent": reduction_percent,
        },
    }
