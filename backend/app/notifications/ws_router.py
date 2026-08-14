import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.database.session import SessionLocal
from app.models.user import User
from app.notifications.ws_manager import manager

router = APIRouter()


def _authenticate(token: str | None) -> User | None:
    """
    30.12: same query-param-token pattern as the energy WebSocket
    (app/realtime/router.py) — a WebSocket handshake has no place for
    an Authorization header on later messages, so the token travels in
    the URL instead. No factory_id to check here (unlike the energy
    socket) since this connection isn't scoped to one factory.
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

        return user
    finally:
        db.close()


@router.websocket("/ws/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    user = _authenticate(token)

    if user is None:
        await websocket.close(code=4401)
        return

    await manager.connect(user.id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)
