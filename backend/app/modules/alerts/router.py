"""STEP 40.40-40.41: Alert & Notification API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import MANAGE_ENERGY
from app.core.dependencies import get_accessible_factory, get_current_user
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User
from app.modules.alerts.oncall import (
    create_on_call_shift,
    get_current_on_call,
    list_on_call_schedule,
)
from app.modules.alerts.schemas import (
    AlertCommentCreate,
    AlertCommentResponse,
    AlertResponse,
    AlertSummaryResponse,
    CurrentOnCallResponse,
    IncidentResponse,
    OnCallShiftCreate,
    OnCallShiftResponse,
    ResolveRequest,
)
from app.modules.alerts.service import (
    acknowledge_alert,
    add_comment,
    get_alert,
    get_alert_summary,
    list_alerts,
    list_incidents,
    resolve_alert,
)

router = APIRouter(
    prefix="/api/v1/factories/{factory_id}/alerts",
    tags=["Alerts & Incidents"],
)


@router.get("", response_model=list[AlertResponse])
def list_alerts_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
):
    return list_alerts(db=db, factory_id=factory.id, status=status)


@router.get("/summary", response_model=AlertSummaryResponse)
def alert_summary(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_alert_summary(db=db, factory_id=factory.id)


# --- On-Call (77.61-77.63) — registered before /{alert_id} so
# "on-call" isn't swallowed by that int-typed path param.


@router.get("/on-call/current", response_model=CurrentOnCallResponse)
def current_on_call_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
    role: str = Query(default="PRIMARY"),
):
    user = get_current_on_call(db, factory.id, role)

    return CurrentOnCallResponse(
        role=role,
        user_id=user.id if user else None,
        user_name=user.full_name if user else None,
        user_email=user.email if user else None,
    )


@router.get("/on-call", response_model=list[OnCallShiftResponse])
def list_on_call_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return list_on_call_schedule(db, factory.id)


@router.post("/on-call", response_model=OnCallShiftResponse, status_code=201)
def create_on_call_endpoint(
    data: OnCallShiftCreate,
    factory: Factory = Depends(get_accessible_factory),
    _current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    return create_on_call_shift(
        db, factory.id, data.user_id, data.role, data.starts_at, data.ends_at
    )


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert_endpoint(
    alert_id: int,
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return get_alert(db=db, alert_id=alert_id, factory_id=factory.id)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_endpoint(
    alert_id: int,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    return acknowledge_alert(db=db, alert_id=alert_id, factory_id=factory.id, user=current_user)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_endpoint(
    alert_id: int,
    data: ResolveRequest,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(require_permission(MANAGE_ENERGY)),
    db: Session = Depends(get_db),
):
    return resolve_alert(db=db, alert_id=alert_id, factory_id=factory.id, user=current_user, reason=data.reason)


@router.post("/{alert_id}/comments", response_model=AlertCommentResponse, status_code=201)
def add_comment_endpoint(
    alert_id: int,
    data: AlertCommentCreate,
    factory: Factory = Depends(get_accessible_factory),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_comment(db=db, alert_id=alert_id, factory_id=factory.id, user=current_user, comment_text=data.comment)


# --- Incidents ---

@router.get("/incidents", response_model=list[IncidentResponse])
def list_incidents_endpoint(
    factory: Factory = Depends(get_accessible_factory),
    db: Session = Depends(get_db),
):
    return list_incidents(db=db, factory_id=factory.id)
