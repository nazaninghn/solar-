"""STEP 81: AI/ML Readiness API — SUPER_ADMIN only, same reasoning as
app/modules/bi, finops, compliance: platform-wide, not any one
organization's own data."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.modules.ai_readiness.data_readiness import (
    compute_data_readiness,
    compute_platform_readiness_summary,
)
from app.modules.ai_readiness.drift_detection import detect_forecast_drift
from app.modules.ai_readiness.model_governance import list_model_registry, seed_model_registry
from app.modules.ai_readiness.schemas import (
    AiReadinessDashboardResponse,
    DataReadinessEntry,
    DriftEntry,
    ModelRegistryEntry,
    ReadinessSummary,
)

router = APIRouter(prefix="/api/v1/ai-readiness", tags=["AI/ML Readiness"])


def _require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Platform admin access required.")
    return current_user


@router.get("/data-readiness", response_model=list[DataReadinessEntry])
def data_readiness_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return [DataReadinessEntry(**row) for row in compute_data_readiness(db)]


@router.get("/model-registry", response_model=list[ModelRegistryEntry])
def model_registry_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return list_model_registry(db)


@router.post("/model-registry/refresh", response_model=list[ModelRegistryEntry])
def refresh_model_registry_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    """Re-scores the registry against the latest ForecastAccuracy
    history — also run automatically (app.jobs.ai_readiness_jobs), this
    endpoint is for an on-demand recheck."""
    return seed_model_registry(db)


@router.get("/drift", response_model=list[DriftEntry])
def drift_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return detect_forecast_drift(db)


@router.get("/dashboard", response_model=AiReadinessDashboardResponse)
def dashboard_endpoint(
    _admin: User = Depends(_require_super_admin),
    db: Session = Depends(get_db),
):
    return AiReadinessDashboardResponse(
        data_readiness_summary=ReadinessSummary(**compute_platform_readiness_summary(db)),
        data_readiness_by_factory=[
            DataReadinessEntry(**row) for row in compute_data_readiness(db)
        ],
        model_registry=list_model_registry(db),
        drift=[DriftEntry(**row) for row in detect_forecast_drift(db)],
    )
