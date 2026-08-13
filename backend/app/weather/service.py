from app.weather.base import WeatherProvider
from app.weather.schemas import WeatherPoint


class WeatherService:
    def __init__(self, provider: WeatherProvider):
        self.provider = provider

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ) -> list[WeatherPoint]:
        return await self.provider.get_forecast(
            latitude=latitude,
            longitude=longitude,
            days=days,
        )
