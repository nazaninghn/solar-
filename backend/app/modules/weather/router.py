from fastapi import APIRouter, Depends

from app.core.dependencies import get_accessible_factory
from app.models.factory import Factory
from app.modules.weather.service import get_factory_weather

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/weather",
    tags=["Weather"],
)


@router.get("")
async def factory_weather(factory: Factory = Depends(get_accessible_factory)):
    return await get_factory_weather(factory)
