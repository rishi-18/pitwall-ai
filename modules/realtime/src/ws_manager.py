from collections import defaultdict

from fastapi import WebSocket

import structlog

log = structlog.get_logger()


class WebSocketManager:

    def __init__(self):

        self.active = defaultdict(set)

    async def connect(
        self,
        ws: WebSocket,
        session_key: int
    ):

        await ws.accept()

        self.active[session_key].add(ws)

        log.info(
            "ws_connected",
            session_key=session_key,
            total=len(self.active[session_key])
        )

    def disconnect(
        self,
        ws: WebSocket,
        session_key: int
    ):

        self.active[session_key].discard(ws)

        log.info(
            "ws_disconnected",
            session_key=session_key,
            remaining=len(self.active[session_key])
        )

    async def broadcast(
        self,
        session_key: int,
        message: dict
    ):

        dead = set()

        for ws in self.active[session_key]:

            try:
                await ws.send_json(message)

            except Exception:
                dead.add(ws)

        for ws in dead:
            self.disconnect(ws, session_key)

    async def send_state_snapshot(
        self,
        ws: WebSocket,
        session_key: int,
        snapshot: dict
    ):

        await ws.send_json({
            "event_type": "snapshot",
            "data": snapshot,
        })


ws_manager = WebSocketManager()
