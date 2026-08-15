"""AI Recommendation API endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.ai.service import get_ai_recommendation

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


@router.get("/recommendation")
async def ai_recommendation(
    solar_kw: float = 350,
    consumption_kw: float = 450,
    battery_soc: float = 55,
    grid_price: float = 0.22,
    cloud_pct: float = 40,
    temperature: float = 28,
):
    """Get AI-powered energy recommendation based on current conditions."""
    result = await get_ai_recommendation(
        solar_kwh=solar_kw,
        consumption_kwh=consumption_kw,
        battery_soc=battery_soc,
        grid_price=grid_price,
        weather_cloud_pct=cloud_pct,
        temperature_c=temperature,
    )
    return result
