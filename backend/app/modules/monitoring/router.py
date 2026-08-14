"""STEP 49.51: Production Monitoring API."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.device import Device
from app.models.user import User
from app.modules.monitoring.models import (
    DeploymentRecord,
    IncidentEvent,
    IncidentPostmortem,
    MonitoringAlertRule,
    MonitoringIncident,
    PostmortemCorrectiveAction,
)
from app.modules.monitoring.schemas import (
    AlertRuleResponse,
    CorrectiveActionCreate,
    CorrectiveActionResponse,
    CorrectiveActionUpdate,
    DeploymentResponse,
    IncidentEventResponse,
    IncidentResponse,
    MonitoringOverviewResponse,
    PostmortemResponse,
    PostmortemUpsert,
)

router = APIRouter(prefix="/api/v1/admin/monitoring", tags=["Production Monitoring"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("SUPER_ADMIN", "COMPANY_ADMIN"):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


@router.get("/overview", response_model=MonitoringOverviewResponse)
def monitoring_overview(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """49.50: Admin monitoring dashboard."""
    active_incidents = db.query(MonitoringIncident).filter(
        MonitoringIncident.status.in_(["OPEN", "ACKNOWLEDGED", "INVESTIGATING"])
    ).count()

    online_devices = db.query(Device).filter(Device.status == "ONLINE").count()

    last_deploy = (
        db.query(DeploymentRecord)
        .order_by(DeploymentRecord.deployed_at.desc())
        .first()
    )

    return MonitoringOverviewResponse(
        system_health="HEALTHY",
        api_requests_per_min=0,
        error_rate_pct=0,
        p95_latency_ms=0,
        active_incidents=active_incidents,
        warning_alerts=0,
        critical_alerts=0,
        online_devices=online_devices,
        queue_size=0,
        last_deployment=last_deploy.version if last_deploy else None,
    )


@router.get("/incidents", response_model=list[IncidentResponse])
def list_incidents(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    query = db.query(MonitoringIncident)
    if status:
        query = query.filter(MonitoringIncident.status == status)
    return query.order_by(MonitoringIncident.started_at.desc()).limit(limit).all()


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    inc = db.query(MonitoringIncident).filter(MonitoringIncident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return inc


@router.get("/incidents/{incident_id}/timeline", response_model=list[IncidentEventResponse])
def incident_timeline(
    incident_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """49.33: Incident timeline."""
    return (
        db.query(IncidentEvent)
        .filter(IncidentEvent.incident_id == incident_id)
        .order_by(IncidentEvent.created_at.asc())
        .all()
    )


@router.post("/incidents/{incident_id}/acknowledge", response_model=IncidentResponse)
def acknowledge_incident(
    incident_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    inc = db.query(MonitoringIncident).filter(MonitoringIncident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    inc.status = "ACKNOWLEDGED"
    inc.acknowledged_at = datetime.now(timezone.utc)
    inc.assigned_to = admin.id
    db.add(IncidentEvent(
        incident_id=inc.id, event_type="ACKNOWLEDGED",
        actor_id=admin.id, message="Incident acknowledged",
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()
    db.refresh(inc)
    return inc


@router.post("/incidents/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(
    incident_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    inc = db.query(MonitoringIncident).filter(MonitoringIncident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    inc.status = "RESOLVED"
    inc.resolved_at = datetime.now(timezone.utc)
    db.add(IncidentEvent(
        incident_id=inc.id, event_type="RESOLVED",
        actor_id=admin.id, message="Incident resolved",
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()
    db.refresh(inc)

    # 77.66-77.68: a soft nudge, not a hard gate — blocking incident
    # resolution on a missing postmortem carries real operational risk
    # (a forgotten form field shouldn't leave a live incident stuck
    # OPEN), so this surfaces as a response flag the caller can act on
    # rather than a 4xx.
    postmortem_required = False
    if inc.severity in ("CRITICAL", "HIGH"):
        existing = (
            db.query(IncidentPostmortem.id)
            .filter(IncidentPostmortem.incident_id == inc.id)
            .first()
        )
        postmortem_required = existing is None

    response = IncidentResponse.model_validate(inc)
    response.postmortem_required = postmortem_required
    return response


# --- Postmortems (77.66-77.68) ---


@router.get("/incidents/{incident_id}/postmortem", response_model=PostmortemResponse)
def get_postmortem(
    incident_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    postmortem = (
        db.query(IncidentPostmortem)
        .filter(IncidentPostmortem.incident_id == incident_id)
        .first()
    )
    if not postmortem:
        raise HTTPException(status_code=404, detail="No postmortem exists for this incident.")
    return postmortem


@router.post("/incidents/{incident_id}/postmortem", response_model=PostmortemResponse)
def upsert_postmortem(
    incident_id: int,
    data: PostmortemUpsert,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Create-or-update — one postmortem per incident, refined over time
    as the investigation progresses rather than filed once and frozen."""
    inc = db.query(MonitoringIncident).filter(MonitoringIncident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")

    postmortem = (
        db.query(IncidentPostmortem)
        .filter(IncidentPostmortem.incident_id == incident_id)
        .first()
    )
    now = datetime.now(timezone.utc)

    if postmortem is None:
        postmortem = IncidentPostmortem(incident_id=incident_id, root_cause=data.root_cause, created_at=now)
        db.add(postmortem)

    postmortem.root_cause = data.root_cause
    postmortem.customer_impact = data.customer_impact
    postmortem.technical_impact = data.technical_impact
    postmortem.timeline = data.timeline
    postmortem.resolution = data.resolution
    postmortem.preventive_actions = data.preventive_actions
    postmortem.owner = data.owner
    postmortem.updated_at = now

    db.commit()
    db.refresh(postmortem)
    return postmortem


@router.get("/postmortems/{postmortem_id}/actions", response_model=list[CorrectiveActionResponse])
def list_corrective_actions(
    postmortem_id: int,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(PostmortemCorrectiveAction)
        .filter(PostmortemCorrectiveAction.postmortem_id == postmortem_id)
        .order_by(PostmortemCorrectiveAction.created_at.asc())
        .all()
    )


@router.post(
    "/postmortems/{postmortem_id}/actions",
    response_model=CorrectiveActionResponse,
    status_code=201,
)
def create_corrective_action(
    postmortem_id: int,
    data: CorrectiveActionCreate,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    postmortem = db.get(IncidentPostmortem, postmortem_id)
    if not postmortem:
        raise HTTPException(status_code=404, detail="Postmortem not found.")

    action = PostmortemCorrectiveAction(
        postmortem_id=postmortem_id,
        description=data.description,
        owner=data.owner,
        priority=data.priority,
        deadline=data.deadline,
        created_at=datetime.now(timezone.utc),
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


@router.patch(
    "/postmortems/{postmortem_id}/actions/{action_id}",
    response_model=CorrectiveActionResponse,
)
def update_corrective_action(
    postmortem_id: int,
    action_id: int,
    data: CorrectiveActionUpdate,
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    action = (
        db.query(PostmortemCorrectiveAction)
        .filter(
            PostmortemCorrectiveAction.id == action_id,
            PostmortemCorrectiveAction.postmortem_id == postmortem_id,
        )
        .first()
    )
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found.")

    action.status = data.status
    db.commit()
    db.refresh(action)
    return action


@router.get("/deployments", response_model=list[DeploymentResponse])
def list_deployments(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return db.query(DeploymentRecord).order_by(DeploymentRecord.deployed_at.desc()).limit(20).all()


@router.get("/alert-rules", response_model=list[AlertRuleResponse])
def list_alert_rules(
    admin: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    return db.query(MonitoringAlertRule).all()
