from app.integrations.weather.client import WeatherClient


class WeatherService:
    def __init__(self):
        self.client = WeatherClient()

    async def get_factory_forecast(
        self,
        latitude: float,
        longitude: float,
    ) -> dict:
        return await self.client.get_forecast(
            latitude=latitude,
            longitude=longitude,
        )
