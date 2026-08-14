"""STEP 36.27: Optimization & Smart Recommendation API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_RECOMMENDATIONS
from app.core.dependencies import get_accessible_factory
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.optimization.models import FlexibleLoad
from app.modules.optimization.schemas import (
    FlexibleLoadCreate,
    FlexibleLoadResponse,
    SmartRecommendationResponse,
)
from app.modules.optimization.service import (
    approve_recommendation,
    cancel_recommendation,
    generate_factory_recommendations,
    get_recommendation,
    get_recommendations,
    reject_recommendation,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/optimization",
    tags=["Optimization"],
)


@router.get("/recommendations", response_model=list[SmartRecommendationResponse])
def list_recommendations(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """List all smart recommendations for a factory."""
    return get_recommendations(db=db, factory_id=factory.id)


@router.post("/recommendations/generate", response_model=list[SmartRecommendationResponse])
def generate_recommendations_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_RECOMMENDATIONS)),
    db: Session = Depends(get_db),
):
    """Trigger recommendation generation."""
    return generate_factory_recommendations(db=db, factory_id=factory.id)


@router.get("/recommendations/{recommendation_id}", response_model=SmartRecommendationResponse)
def get_recommendation_detail(
    recommendation_id: int,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_recommendation(db=db, recommendation_id=recommendation_id, factory_id=factory.id)


@router.post("/recommendations/{recommendation_id}/approve", response_model=SmartRecommendationResponse)
def approve_endpoint(
    recommendation_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_RECOMMENDATIONS)),
    db: Session = Depends(get_db),
):
    """36.26: Approve a recommendation."""
    return approve_recommendation(
        db=db, recommendation_id=recommendation_id, factory_id=factory.id, user=current_user
    )


@router.post("/recommendations/{recommendation_id}/reject", response_model=SmartRecommendationResponse)
def reject_endpoint(
    recommendation_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_RECOMMENDATIONS)),
    db: Session = Depends(get_db),
):
    return reject_recommendation(
        db=db, recommendation_id=recommendation_id, factory_id=factory.id, user=current_user
    )


@router.post("/recommendations/{recommendation_id}/cancel", response_model=SmartRecommendationResponse)
def cancel_endpoint(
    recommendation_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_RECOMMENDATIONS)),
    db: Session = Depends(get_db),
):
    return cancel_recommendation(
        db=db, recommendation_id=recommendation_id, factory_id=factory.id, user=current_user
    )


# --- Flexible Loads ---

@router.get("/flexible-loads", response_model=list[FlexibleLoadResponse])
def list_flexible_loads(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    """36.19: List factory flexible loads."""
    return db.query(FlexibleLoad).filter(FlexibleLoad.factory_id == factory.id).all()


@router.post("/flexible-loads", response_model=FlexibleLoadResponse, status_code=201)
def create_flexible_load(
    data: FlexibleLoadCreate,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_RECOMMENDATIONS)),
    db: Session = Depends(get_db),
):
    load = FlexibleLoad(
        factory_id=factory.id,
        name=data.name,
        power_kw=data.power_kw,
        energy_kwh=data.energy_kwh,
        earliest_start=data.earliest_start,
        latest_end=data.latest_end,
        duration_minutes=data.duration_minutes,
        priority=data.priority,
    )
    db.add(load)
    db.commit()
    db.refresh(load)
    return load
