from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.modules.battery.schemas import (
    BatteryCreate,
    BatteryRecommendationResponse,
    BatteryResponse,
)
from app.modules.battery.service import (
    create_battery,
    get_battery,
    get_battery_recommendation,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/battery",
    tags=["Battery"],
)


@router.post("", response_model=BatteryResponse, status_code=status.HTTP_201_CREATED)
def create_battery_endpoint(
    data: BatteryCreate,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return create_battery(db=db, factory_id=factory.id, data=data)


@router.get("", response_model=BatteryResponse)
def get_battery_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_battery(db=db, factory_id=factory.id)


@router.get("/recommendation", response_model=BatteryRecommendationResponse)
async def battery_recommendation_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return await get_battery_recommendation(db=db, factory=factory)
