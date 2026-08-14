from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.permissions import role_has_permission
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.modules.security.audit_service import EVENT_PERMISSION_DENIED, log_security_event


def require_permission(permission: str):
    """
    24.20's actual point: check a named permission, not
    `if user.role == "..."` scattered across every endpoint.

    Usage: Depends(require_permission(MANAGE_FACTORY_SETTINGS))
    """

    def _check(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not role_has_permission(current_user.role, permission):
            log_security_event(
                db,
                event_type=EVENT_PERMISSION_DENIED,
                severity="INFO",
                user_id=current_user.id,
                organization_id=current_user.organization_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                description=f"Missing required permission: {permission}",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}",
            )

        return current_user

    return _check
