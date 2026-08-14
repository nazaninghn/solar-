from collections import defaultdict

from fastapi import WebSocket


class NotificationConnectionManager:
    """
    30.12: unlike the energy WebSocket (app/realtime/manager.py, keyed
    by factory_id — one dashboard screen, one factory), this is keyed by
    user_id. The notification bell (30.7) needs every alert across
    every factory a user can reach, not just whichever one they're
    currently viewing.
    """

    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        self.connections[user_id].discard(websocket)

    async def send_to_user(self, user_id: int, message: dict) -> None:
        dead_connections = []

        for websocket in self.connections.get(user_id, set()):
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.append(websocket)

        for websocket in dead_connections:
            self.disconnect(user_id, websocket)


manager = NotificationConnectionManager()


async def broadcast_notification_to_users(notification, user_ids: list[int]) -> None:
    """
    30.13: factory_id-scoped at the source — dispatch_notification_
    deliveries only ever passes user_ids it already resolved via
    list_users_with_factory_access for THIS notification's own factory,
    so a factory-B user's connection is never even considered here for
    a factory-A alert. There's no separate "which factory does this
    user currently have open" filtering step, because there doesn't
    need to be — the eligible-user list was already correct going in.
    """
    message = {
        "type": "NOTIFICATION",
        "data": {
            "id": notification.id,
            "factory_id": notification.factory_id,
            "notification_type": notification.type,
            "severity": notification.severity,
            "priority": notification.priority,
            "title": notification.title,
            "message": notification.message,
            "alert_metadata": notification.alert_metadata,
            "created_at": notification.created_at.isoformat(),
        },
    }

    for user_id in user_ids:
        await manager.send_to_user(user_id, message)
