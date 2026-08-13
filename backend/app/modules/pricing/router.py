from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.modules.pricing.schemas import (
    ElectricityPriceCreate,
    ElectricityPriceResponse,
    PriceAnalysisResponse,
)
from app.modules.pricing.service import create_price, get_price_analysis, get_prices

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/electricity-prices",
    tags=["Electricity Prices"],
)


@router.post(
    "",
    response_model=ElectricityPriceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_electricity_price(
    data: ElectricityPriceCreate,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return create_price(db=db, factory_id=factory.id, data=data)


@router.get("", response_model=list[ElectricityPriceResponse])
def list_electricity_prices(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_prices(db=db, factory_id=factory.id, start=start, end=end)


@router.get("/analysis", response_model=PriceAnalysisResponse)
def electricity_price_analysis(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_price_analysis(db=db, factory_id=factory.id)
