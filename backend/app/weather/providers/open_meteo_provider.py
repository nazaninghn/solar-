from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.weather.base import WeatherProvider
from app.weather.schemas import WeatherPoint


def _condition_from_cloud_cover(cloud_cover: float) -> str:
    if cloud_cover <= 10:
        return "CLEAR"
    if cloud_cover <= 30:
        return "MOSTLY_CLEAR"
    if cloud_cover <= 50:
        return "PARTLY_CLOUDY"
    if cloud_cover <= 70:
        return "CLOUDY"
    if cloud_cover <= 90:
        return "VERY_CLOUDY"
    return "OVERCAST"


class OpenMeteoProvider(WeatherProvider):
    """
    Named for the concrete provider rather than the brief's literal
    providers/provider.py — a file called "provider.py" holding one
    specific provider's implementation reads oddly once a second
    provider exists. The interface (WeatherProvider, app/weather/base.py)
    is what the DoD checklist actually cares about being swappable.

    Unlike Step 8's WeatherClient (which only requested hourly
    cloud_cover), this requests the full variable set 19.4's WeatherPoint
    schema needs — including shortwave_radiation, the real proxy for
    solar irradiance that 19.15's physical model depends on.
    """

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> list[WeatherPoint]:
        url = f"{settings.WEATHER_BASE_URL}/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": (
                "temperature_2m,cloud_cover,relative_humidity_2m,"
                "wind_speed_10m,shortwave_radiation"
            ),
            "forecast_days": days,
            "timezone": "UTC",
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        clouds = hourly.get("cloud_cover", [])
        humidity = hourly.get("relative_humidity_2m", [])
        wind = hourly.get("wind_speed_10m", [])
        irradiance = hourly.get("shortwave_radiation", [])

        points = []

        for i, time_str in enumerate(times):
            cloud_cover = clouds[i] if i < len(clouds) else 0.0

            # Open-Meteo returns naive "2026-08-14T10:00" strings even
            # with timezone=UTC requested — attach tzinfo explicitly so
            # this doesn't silently become ambiguous against our
            # timezone-aware DB columns.
            points.append(
                WeatherPoint(
                    timestamp=datetime.fromisoformat(time_str).replace(
                        tzinfo=timezone.utc
                    ),
                    temperature_c=temps[i] if i < len(temps) else 0.0,
                    cloud_cover_percent=cloud_cover,
                    humidity_percent=humidity[i] if i < len(humidity) else 0.0,
                    wind_speed_mps=wind[i] if i < len(wind) else 0.0,
                    solar_irradiance_w_m2=(
                        irradiance[i] if i < len(irradiance) else None
                    ),
                    condition=_condition_from_cloud_cover(cloud_cover),
                )
            )

        return points
