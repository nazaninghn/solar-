import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.access_control import can_access_factory
from app.core.security import decode_token
from app.database.session import get_db
from app.models.factory import Factory
from app.models.user import User

bearer_scheme = HTTPBearer()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    # A refresh token is valid JWT but must never be accepted where an
    # access token is expected — otherwise a leaked refresh token becomes
    # a long-lived access token by accident.
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = db.get(User, int(user_id))

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # 28.6: request-scoped state, read back by RequestLoggingMiddleware
    # after the route handler returns — the middleware runs outside
    # FastAPI's dependency-injection cycle, so it can't know who the
    # caller was except by a side channel like this.
    request.state.user_id = user.id
    request.state.organization_id = user.organization_id

    return user


def get_accessible_factory(
    factory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Factory:
    """
    Factory-level tenant isolation, extended in Step 24 with per-user
    factory scoping (24.7) on top of the existing organization boundary.

    Two distinct failure modes, two distinct status codes (confirmed
    explicitly with the user when Step 24 introduced this split):

    - Cross-organization (SUPER_ADMIN excepted): 404, unchanged from
      Step 5's original reasoning — a 403 would confirm to the caller
      that `factory_id` exists somewhere, even in a tenant they have no
      relationship to at all. 404 makes "not yours" indistinguishable
      from "doesn't exist".
    - Same organization, but this specific user isn't assigned to this
      factory (non-admin roles only, via user_factory_access): 403 —
      the company itself already has a legitimate relationship to this
      factory, so its existence isn't secret from this user the way an
      entirely different tenant's data would be.
    """
    factory = db.get(Factory, factory_id)

    if factory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factory not found",
        )

    if current_user.role != "SUPER_ADMIN" and factory.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factory not found",
        )

    if not can_access_factory(db, current_user, factory):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this factory",
        )

    return factory
