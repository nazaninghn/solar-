from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.modules.production_lines.schemas import (
    ProductionLineCreate,
    ProductionLineResponse,
)
from app.modules.production_lines.service import (
    create_production_line,
    get_production_lines,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/production-lines",
    tags=["Production Lines"],
)


@router.get("", response_model=list[ProductionLineResponse])
def list_production_lines(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_production_lines(db=db, factory_id=factory.id)


@router.post(
    "", response_model=ProductionLineResponse, status_code=status.HTTP_201_CREATED
)
def create_production_line_endpoint(
    data: ProductionLineCreate,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return create_production_line(db=db, factory_id=factory.id, data=data)
