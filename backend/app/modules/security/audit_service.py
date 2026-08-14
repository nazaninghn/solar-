"""
STEP 53.50-53.52: Security Audit Service.

Logs security-sensitive events. Audit logs are append-only.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.security.models import SecurityEvent

logger = logging.getLogger(__name__)


def log_security_event(
    db: Session,
    event_type: str,
    severity: str = "INFO",
    user_id: int | None = None,
    organization_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    description: str | None = None,
    metadata_json: str | None = None,
) -> SecurityEvent:
    """
    53.50: Record a security event.
    These events are immutable — no update/delete.
    """
    event = SecurityEvent(
        user_id=user_id,
        organization_id=organization_id,
        event_type=event_type,
        severity=severity,
        ip_address=ip_address,
        user_agent=user_agent,
        description=description,
        metadata_json=metadata_json,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()

    if severity in ("HIGH", "CRITICAL"):
        logger.warning(
            f"Security event: {event_type} severity={severity} user={user_id} ip={ip_address}",
            extra={"event_type": event_type, "user_id": user_id, "ip": ip_address},
        )

    return event


# Pre-defined event types for consistency
EVENT_LOGIN_FAILED = "LOGIN_FAILED"
EVENT_LOGIN_SUCCESS = "LOGIN_SUCCESS"
EVENT_MFA_FAILED = "MFA_FAILED"
EVENT_PASSWORD_CHANGED = "PASSWORD_CHANGED"
EVENT_PASSWORD_RESET = "PASSWORD_RESET_REQUESTED"
EVENT_PERMISSION_DENIED = "PERMISSION_DENIED"
EVENT_TOKEN_REUSE = "TOKEN_REUSE"
EVENT_ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
EVENT_ROLE_CHANGED = "ROLE_CHANGED"
EVENT_API_KEY_CREATED = "API_KEY_CREATED"
EVENT_API_KEY_REVOKED = "API_KEY_REVOKED"
EVENT_ADMIN_ACTION = "ADMIN_ACTION"
EVENT_SUSPICIOUS_REQUEST = "SUSPICIOUS_REQUEST"
EVENT_RATE_LIMIT_HIT = "RATE_LIMIT_EXCEEDED"
EVENT_IDOR_ATTEMPT = "IDOR_ATTEMPT"
EVENT_INJECTION_ATTEMPT = "INJECTION_ATTEMPT"
