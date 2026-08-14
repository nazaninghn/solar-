"""
82: consumption side of the APIKey model (created 46.30-46.31, only ever
issued/revoked via the admin panel until now — a service-identity
credential with nothing checking it on any request path). Mirrors
app/devices/auth.py's shape (hash the presented secret, look up by
hash, check revocation) since that's this codebase's one other
non-user credential type, just organization-scoped instead of
device-scoped.
"""

from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.database.session import get_db
from app.models.organization import Organization
from app.modules.admin.models import APIKey
from app.modules.security.audit_service import EVENT_SUSPICIOUS_REQUEST, log_security_event


def get_organization_from_api_key(
    request: Request,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None),
) -> Organization:
    """
    Authenticates the caller as an ORGANIZATION, not a user — same
    "proves identity, nothing more" shape as device keys. Deliberately
    used only for read-only, org-scoped integration endpoints: an API
    key is a machine credential with no concept of "which human, which
    role", so it can't stand in for require_permission()'s per-role
    checks the way a user JWT can.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    key = db.scalar(
        select(APIKey).where(APIKey.hashed_key == hash_token(x_api_key))
    )

    now = datetime.now(timezone.utc)
    invalid = (
        key is None
        or key.revoked_at is not None
        or (key.expires_at is not None and key.expires_at < now)
    )

    if invalid:
        log_security_event(
            db,
            event_type=EVENT_SUSPICIOUS_REQUEST,
            severity="INFO",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            description="Invalid, revoked, or expired API key presented",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, revoked, or expired API key",
        )

    key.last_used_at = now
    db.commit()

    organization = db.get(Organization, key.organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key's organization no longer exists",
        )

    return organization
