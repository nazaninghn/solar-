import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)
        # Not in the brief: something has to decide when
        # simulate_factory_energy actually runs. Starting one task per
        # factory at app startup would mean an infinite loop running
        # forever for factories nobody's watching; instead, a simulator
        # starts on the first connection to a factory and stops once the
        # last client for that factory disconnects.
        self._simulator_tasks: dict[int, asyncio.Task] = {}

    async def connect(self, factory_id: int, websocket: WebSocket):
        await websocket.accept()

        self.connections[factory_id].add(websocket)
        self._ensure_simulator_running(factory_id)

    def disconnect(self, factory_id: int, websocket: WebSocket):
        self.connections[factory_id].discard(websocket)

        if not self.connections[factory_id]:
            self._stop_simulator(factory_id)

    async def broadcast(self, factory_id: int, message: dict):
        dead_connections = []

        for websocket in self.connections[factory_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.append(websocket)

        for websocket in dead_connections:
            self.disconnect(factory_id, websocket)

    def _ensure_simulator_running(self, factory_id: int) -> None:
        if factory_id in self._simulator_tasks:
            return

        # Step 16 (16.20-16.21): once a factory has real (or
        # real-simulated) Devices configured, the Device Gateway polling
        # loop becomes the source of truth and broadcasts to this same
        # factory_id itself — running the old per-connection ad-hoc
        # simulator at the same time produced two independent random
        # sources fighting over the same WebSocket, which is worse than
        # either alone. So this fallback is now conditional: it only
        # starts for factories that have no active Device rows yet,
        # preserving zero-config demo behavior for those, while stepping
        # aside once a factory actually onboards devices.
        from sqlalchemy import exists, select

        from app.database.session import SessionLocal
        from app.models.device import Device

        db = SessionLocal()
        try:
            has_devices = db.scalar(
                select(
                    exists().where(
                        Device.factory_id == factory_id,
                        Device.is_active.is_(True),
                    )
                )
            )
        finally:
            db.close()

        if has_devices:
            return

        # Deferred import to avoid a circular import: simulator.py
        # imports `manager` from this module at its own top level.
        from app.realtime.simulator import simulate_factory_energy

        self._simulator_tasks[factory_id] = asyncio.create_task(
            simulate_factory_energy(factory_id)
        )

    def _stop_simulator(self, factory_id: int) -> None:
        task = self._simulator_tasks.pop(factory_id, None)

        if task:
            task.cancel()


manager = ConnectionManager()
