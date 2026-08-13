from fastapi import HTTPException, status

from app.integrations.weather.service import WeatherService
from app.models.factory import Factory


async def get_factory_weather(factory: Factory) -> dict:
    if factory.latitude is None or factory.longitude is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Factory location is not configured",
        )

    weather_service = WeatherService()

    return await weather_service.get_factory_forecast(
        latitude=factory.latitude,
        longitude=factory.longitude,
    )
