from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def log_audit_action(
    db: Session,
    user: User,
    action: str,
    resource_type: str,
    resource_id: int | None = None,
    request: Request | None = None,
) -> None:
    """24.33-24.34: called from mutating admin endpoints (user
    management, company/factory settings) right before the commit that
    performs the change, so the log entry and the change share a
    transaction."""
    db.add(
        AuditLog(
            user_id=user.id,
            organization_id=user.organization_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            created_at=datetime.now(timezone.utc),
        )
    )
