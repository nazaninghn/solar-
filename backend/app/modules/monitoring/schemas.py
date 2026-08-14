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
