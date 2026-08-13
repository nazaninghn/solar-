import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.database.session import SessionLocal
from app.models.factory import Factory
from app.models.user import User
from app.realtime.manager import manager

router = APIRouter()


def _authenticate(factory_id: int, token: str | None) -> tuple[User, Factory] | None:
    """
    15.14-15.15 explicitly call unauthenticated WebSocket access
    "forbidden in production", and it's on the Step 15 DoD list, so this
    is implemented now rather than left as a known gap. Mirrors
    get_current_user + get_accessible_factory's checks, adapted for a
    query-param token since a WebSocket handshake has no place for the
    usual Authorization header on subsequent messages.
    """
    if not token:
        return None

    try:
        payload = decode_token(token)
    except jwt.InvalidTokenError:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    db = SessionLocal()
    try:
        user = db.get(User, int(user_id))
        if user is None or not user.is_active:
            return None

        factory = db.get(Factory, factory_id)
        if factory is None or factory.organization_id != user.organization_id:
            return None

        return user, factory
    finally:
        db.close()


@router.websocket("/ws/factories/{factory_id}/energy")
async def energy_websocket(
    websocket: WebSocket,
    factory_id: int,
    token: str | None = Query(default=None),
):
    auth_result = _authenticate(factory_id, token)

    if auth_result is None:
        # Reject before accept() — sends a close frame without ever
        # completing the handshake, the WebSocket equivalent of a 401.
        await websocket.close(code=4401)
        return

    await manager.connect(factory_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(factory_id, websocket)
