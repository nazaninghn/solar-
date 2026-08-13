from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.recommendations.schemas import RecommendationResponse, RejectRequest
from app.modules.recommendations.service import (
    accept_recommendation,
    generate_factory_recommendations,
    get_recommendation_detail,
    get_recommendations,
    reject_recommendation,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/recommendations",
    tags=["Recommendations"],
)


@router.get("", response_model=list[RecommendationResponse])
async def list_recommendations(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    await generate_factory_recommendations(db=db, factory=factory)

    return get_recommendations(db=db, factory_id=factory.id)


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def recommendation_detail(
    recommendation_id: int,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_recommendation_detail(
        db=db, factory_id=factory.id, recommendation_id=recommendation_id
    )


@router.post("/{recommendation_id}/accept", response_model=RecommendationResponse)
def accept_recommendation_endpoint(
    recommendation_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return accept_recommendation(
        db=db,
        factory_id=factory.id,
        recommendation_id=recommendation_id,
        current_user=current_user,
    )


@router.post("/{recommendation_id}/reject", response_model=RecommendationResponse)
def reject_recommendation_endpoint(
    recommendation_id: int,
    data: RejectRequest,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return reject_recommendation(
        db=db,
        factory_id=factory.id,
        recommendation_id=recommendation_id,
        current_user=current_user,
        reason=data.reason,
    )
