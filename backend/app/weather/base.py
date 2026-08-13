from abc import ABC, abstractmethod


class WeatherProvider(ABC):
    @abstractmethod
    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
    ):
        pass
