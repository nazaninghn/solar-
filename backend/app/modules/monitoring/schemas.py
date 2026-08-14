"""STEP 49: Monitoring schemas."""

from datetime import datetime
from pydantic import BaseModel


class IncidentResponse(BaseModel):
    id: int
    title: str
    severity: str
    status: str
    service: str | None
    started_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    root_cause: str | None
    # 77.66-77.68: only ever explicitly set (True/False) by the resolve
    # endpoint for CRITICAL/HIGH incidents — everywhere else this
    # response shape is reused it just carries the unpopulated default.
    postmortem_required: bool = False
    model_config = {"from_attributes": True}


class PostmortemUpsert(BaseModel):
    root_cause: str
    customer_impact: str | None = None
    technical_impact: str | None = None
    timeline: str | None = None
    resolution: str | None = None
    preventive_actions: str | None = None
    owner: str | None = None


class PostmortemResponse(BaseModel):
    id: int
    incident_id: int
    root_cause: str
    customer_impact: str | None
    technical_impact: str | None
    timeline: str | None
    resolution: str | None
    preventive_actions: str | None
    owner: str | None
    created_at: datetime
    updated_at: datetime | None
    model_config = {"from_attributes": True}


class CorrectiveActionCreate(BaseModel):
    description: str
    owner: str | None = None
    priority: str = "MEDIUM"
    deadline: datetime | None = None


class CorrectiveActionUpdate(BaseModel):
    status: str


class CorrectiveActionResponse(BaseModel):
    id: int
    postmortem_id: int
    description: str
    owner: str | None
    priority: str
    deadline: datetime | None
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class IncidentEventResponse(BaseModel):
    id: int
    event_type: str
    message: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class MonitoringOverviewResponse(BaseModel):
    system_health: str
    api_requests_per_min: float
    error_rate_pct: float
    p95_latency_ms: float
    active_incidents: int
    warning_alerts: int
    critical_alerts: int
    online_devices: int
    queue_size: int
    last_deployment: str | None


class DeploymentResponse(BaseModel):
    id: int
    version: str
    commit_sha: str | None
    environment: str
    status: str
    deployed_at: datetime
    model_config = {"from_attributes": True}


class AlertRuleResponse(BaseModel):
    id: int
    name: str
    metric: str
    operator: str
    threshold: float
    severity: str
    enabled: bool
    model_config = {"from_attributes": True}
