from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.devices.scenario import VALID_SCENARIOS, get_scenario, set_scenario
from app.models.user import User
from app.modules.system.schemas import (
    JobStatusListResponse,
    JobStatusResponse,
    ScenarioRequest,
    ScenarioResponse,
)
from app.modules.system.service import get_latest_job_statuses

router = APIRouter(
    prefix="/api/v1/system",
    tags=["System"],
)


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    25.34's job data has no organization_id — it's platform-wide
    background-job execution across every company's factories, not one
    company's data. Gating this with the existing require_permission()
    would let any COMPANY_ADMIN see it too (ALL_PERMISSIONS includes
    everything in the matrix), which would leak operational data about
    companies they have no relationship to. SUPER_ADMIN only.
    """
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is restricted to platform administrators",
        )

    return current_user


@router.get("/jobs", response_model=JobStatusListResponse)
def get_job_statuses(
    _current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    job_runs = get_latest_job_statuses(db)

    return JobStatusListResponse(
        jobs=[
            JobStatusResponse(
                name=job_run.job_name,
                status=job_run.status,
                last_run=job_run.started_at,
                duration_ms=job_run.duration_ms,
                error_message=job_run.error_message,
            )
            for job_run in job_runs
        ]
    )


@router.get("/simulator-scenario", response_model=ScenarioResponse)
def get_simulator_scenario(
    _current_user: User = Depends(require_super_admin),
):
    return ScenarioResponse(
        scenario=get_scenario(), valid_scenarios=sorted(VALID_SCENARIOS)
    )


@router.put("/simulator-scenario", response_model=ScenarioResponse)
def update_simulator_scenario(
    data: ScenarioRequest,
    _current_user: User = Depends(require_super_admin),
):
    """
    26.37, a testing tool: switches every SIMULATOR-connected device's
    behavior process-wide (not per-company), so it's SUPER_ADMIN-gated
    the same way /system/jobs is — a COMPANY_ADMIN flipping this would
    disrupt every other company's simulated data too.
    """
    try:
        set_scenario(data.scenario)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    return ScenarioResponse(
        scenario=get_scenario(), valid_scenarios=sorted(VALID_SCENARIOS)
    )
