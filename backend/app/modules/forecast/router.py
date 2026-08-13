from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.forecast.schemas import EnergyForecastResponse, SolarForecastResponse
from app.forecast.service import get_energy_forecast, get_solar_forecast
from app.models.factory import Factory
from app.modules.forecast.schemas import FactoryForecastResponse
from app.modules.forecast.service import get_factory_forecast

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/forecast",
    tags=["Forecast"],
)


@router.get("", response_model=FactoryForecastResponse)
async def factory_forecast(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return await get_factory_forecast(db=db, factory=factory)


# 19.26-19.27: hourly forecast series (Step 19), distinct from the
# single-day aggregate above (Step 8, still used by Recommendations/
# Battery/Notifications) — same router/prefix, different sub-paths.
@router.get("/solar", response_model=SolarForecastResponse)
async def solar_forecast(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    forecast, is_stale = await get_solar_forecast(db=db, factory=factory)

    return {
        "factory_id": factory.id,
        "is_stale": is_stale,
        "forecast": forecast,
    }


@router.get("/energy", response_model=EnergyForecastResponse)
async def energy_forecast(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    forecast, is_stale = await get_energy_forecast(db=db, factory=factory)

    return {
        "factory_id": factory.id,
        "is_stale": is_stale,
        "forecast": forecast,
    }
