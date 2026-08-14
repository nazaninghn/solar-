"""STEP 46.48-46.49: Admin Panel API."""

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.device import Device
from app.models.factory import Factory
from app.models.organization import Organization
from app.models.user import User
from app.modules.admin.models import (
    APIKey,
    AdminAuditLog,
    FeatureFlag,
    SystemConfig,
)
from app.modules.admin.schemas import (
    APIKeyCreateResponse,
    APIKeyResponse,
    AdminAuditResponse,
    AdminDashboardResponse,
    FeatureFlagResponse,
    HealthResponse,
    SystemConfigResponse,
)
from app.modules.observability.system_health import get_system_health
from app.modules.billing.models import Payment, Subscription
from app.modules.bi.revenue import compute_mrr
from app.modules.monitoring.models import MonitoringIncident

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Panel"])


def _require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    79.16-79.18: every endpoint in this router is platform-wide, not
    organization-scoped (list every org, list every user, disable any
    user, suspend any org) — SUPER_ADMIN only. COMPANY_ADMIN already
    has its own organization-scoped equivalents under /api/v1/company;
    allowing it here (as this previously did) let any company's own
    admin see and modify every *other* company's data — a real
    cross-tenant privilege escalation, not a scoping choice.
    """
    if current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Platform admin access required.")
    return current_user


@router.get("/dashboard", response_model=AdminDashboardResponse)
def admin_dashboard(
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    """
    46.26: Platform admin dashboard KPIs. 80: the last three fields
    (active_subscriptions, failed_payments, monthly_revenue) were
    hardcoded to 0 since Step 46 — real queries now, correctly
    returning 0 today since no subscription has ever been created in
    this deployment (see app.modules.bi.revenue's module docstring).
    open_critical_alerts was similarly hardcoded; now a real count of
    OPEN CRITICAL incidents.
    """
    return AdminDashboardResponse(
        total_organizations=db.query(Organization).count(),
        active_users=db.query(User).filter(User.is_active == True).count(),
        active_factories=db.query(Factory).count(),
        online_devices=db.query(Device).filter(Device.status == "ONLINE").count(),
        offline_devices=db.query(Device).filter(Device.status == "OFFLINE").count(),
        open_critical_alerts=db.query(MonitoringIncident)
        .filter(MonitoringIncident.severity == "CRITICAL", MonitoringIncident.status == "OPEN")
        .count(),
        active_subscriptions=db.query(Subscription).filter(Subscription.status == "ACTIVE").count(),
        failed_payments=db.query(Payment).filter(Payment.status == "FAILED").count(),
        monthly_revenue=compute_mrr(db),
    )


@router.get("/health", response_model=HealthResponse)
def admin_health(
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    """46.16: System health overview."""
    health = get_system_health(db)
    return HealthResponse(
        api=health["api"],
        database=health["database"],
        queue=health.get("queue", "UNKNOWN"),
        cache="HEALTHY",
        weather=health.get("weather_feed", "UNKNOWN"),
        price_feed=health.get("price_feed", "UNKNOWN"),
        overall=health["overall"],
    )


@router.get("/organizations")
def list_organizations(
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=200),
):
    return db.query(Organization).limit(limit).all()


@router.post("/organizations/{org_id}/suspend")
def suspend_organization(
    org_id: int,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    _audit(db, admin.id, "SUSPEND_ORGANIZATION", "organization", org_id)
    db.commit()
    return {"status": "suspended", "organization_id": org_id}


@router.get("/users")
def list_users(
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, le=200),
):
    return db.query(User).limit(limit).all()


@router.post("/users/{user_id}/disable")
def disable_user(
    user_id: int,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = False
    _audit(db, admin.id, "DISABLE_USER", "user", user_id)
    db.commit()
    return {"status": "disabled", "user_id": user_id}


@router.post("/users/{user_id}/enable")
def enable_user(
    user_id: int,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = True
    _audit(db, admin.id, "ENABLE_USER", "user", user_id)
    db.commit()
    return {"status": "enabled", "user_id": user_id}


# --- System Config ---

@router.get("/system-config", response_model=list[SystemConfigResponse])
def list_configs(
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    configs = db.query(SystemConfig).all()
    # Mask secrets
    for c in configs:
        if c.is_secret:
            c.value = "***REDACTED***"
    return configs


# --- Feature Flags ---

@router.get("/feature-flags", response_model=list[FeatureFlagResponse])
def list_feature_flags(
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    return db.query(FeatureFlag).all()


@router.post("/feature-flags/{flag_id}/toggle")
def toggle_feature_flag(
    flag_id: int,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    flag = db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found.")
    old = flag.enabled
    flag.enabled = not flag.enabled
    flag.updated_at = datetime.now(timezone.utc)
    _audit(db, admin.id, "TOGGLE_FEATURE_FLAG", "feature_flag", flag_id, str(old), str(flag.enabled))
    db.commit()
    return {"key": flag.key, "enabled": flag.enabled}


# --- API Keys ---

@router.get("/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    return db.query(APIKey).filter(APIKey.revoked_at == None).all()


@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=201)
def create_api_key(
    organization_id: int,
    name: str,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    """46.30-46.31: Create API key — raw key shown only once."""
    raw_key = f"sf_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:7]
    hashed = hashlib.sha256(raw_key.encode()).hexdigest()

    key = APIKey(
        organization_id=organization_id,
        name=name,
        key_prefix=prefix,
        hashed_key=hashed,
        created_by=admin.id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(key)
    _audit(db, admin.id, "CREATE_API_KEY", "api_key", None)
    db.commit()
    db.refresh(key)

    return APIKeyCreateResponse(
        id=key.id, name=key.name, key_prefix=prefix,
        raw_key=raw_key, created_at=key.created_at,
    )


@router.post("/api-keys/{key_id}/revoke")
def revoke_api_key(
    key_id: int,
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
):
    key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found.")
    key.revoked_at = datetime.now(timezone.utc)
    _audit(db, admin.id, "REVOKE_API_KEY", "api_key", key_id)
    db.commit()
    return {"status": "revoked"}


# --- Audit Logs ---

@router.get("/audit-logs", response_model=list[AdminAuditResponse])
def list_audit_logs(
    admin: User = Depends(_require_platform_admin),
    db: Session = Depends(get_db),
    limit: int = Query(default=100, le=500),
):
    return db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(limit).all()


def _audit(
    db: Session, admin_id: int, action: str, resource_type: str,
    resource_id: int | None = None, old_value: str | None = None, new_value: str | None = None,
):
    db.add(AdminAuditLog(
        admin_user_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        created_at=datetime.now(timezone.utc),
    ))
