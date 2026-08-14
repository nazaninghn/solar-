"""STEP 46: Admin schemas."""

from datetime import datetime

from pydantic import BaseModel


class AdminDashboardResponse(BaseModel):
    total_organizations: int
    active_users: int
    active_factories: int
    online_devices: int
    offline_devices: int
    open_critical_alerts: int
    active_subscriptions: int
    failed_payments: int
    monthly_revenue: float


class SystemConfigResponse(BaseModel):
    id: int
    key: str
    value: str
    type: str
    description: str | None
    is_secret: bool
    model_config = {"from_attributes": True}


class FeatureFlagResponse(BaseModel):
    id: int
    key: str
    enabled: bool
    environment: str
    organization_id: int | None
    rollout_percentage: int
    model_config = {"from_attributes": True}


class APIKeyResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    key_prefix: str
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class APIKeyCreateResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    raw_key: str  # Only shown once at creation
    created_at: datetime


class AdminAuditResponse(BaseModel):
    id: int
    admin_user_id: int
    action: str
    resource_type: str
    resource_id: int | None
    ip_address: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    api: str
    database: str
    queue: str
    cache: str
    weather: str
    price_feed: str
    overall: str
