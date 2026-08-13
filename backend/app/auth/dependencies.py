from fastapi import Depends, HTTPException, status

from app.auth.permissions import role_has_permission
from app.core.dependencies import get_current_user
from app.models.user import User


def require_permission(permission: str):
    """
    24.20's actual point: check a named permission, not
    `if user.role == "..."` scattered across every endpoint.

    Usage: Depends(require_permission(MANAGE_FACTORY_SETTINGS))
    """

    def _check(current_user: User = Depends(get_current_user)) -> User:
        if not role_has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}",
            )

        return current_user

    return _check
