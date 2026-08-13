import httpx

from app.core.config import settings


class WeatherClient:
    """
    Provider: Open-Meteo (https://open-meteo.com), chosen for Step 8
    because it needs no API key, so the integration is testable without
    a paid account. WEATHER_API_KEY is kept in config for a future
    provider swap; Open-Meteo itself ignores it.
    """

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:
        url = f"{settings.WEATHER_BASE_URL}/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "cloud_cover",
            "forecast_days": 2,
            "timezone": "UTC",
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            return response.json()
