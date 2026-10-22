from __future__ import annotations

import time
import uuid
import logging
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

from backend.websocket.schemas import ServerMessage

log = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._active: dict[str, tuple[WebSocket, float]] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        session_id = uuid.uuid4().hex[:12]
        self._active[session_id] = (websocket, time.time())
        try:
            await websocket.send_json(
                ServerMessage(
                    type="welcome",
                    session_id=session_id,
                    message="SilentLink WebSocket connected. Send {type:'frame'} with landmark data.",
                    ts=time.time(),
                ).model_dump(exclude_none=True)
            )
        except Exception as e:
            log.warning("welcome send failed %s", e)
        log.info("websocket connect session=%s active=%d", session_id, len(self._active))
        return session_id

    def disconnect(self, session_id: str) -> None:
        if session_id in self._active:
            del self._active[session_id]
            log.info("websocket disconnect session=%s active=%d", session_id, len(self._active))

    async def send(self, session_id: str, payload: dict) -> bool:
        entry = self._active.get(session_id)
        if entry is None:
            return False
        ws, _ts = entry
        try:
            await ws.send_json(payload)
            self._active[session_id] = (ws, time.time())
            return True
        except (WebSocketDisconnect, RuntimeError) as e:
            log.debug("send error session=%s %s", session_id, e)
            self.disconnect(session_id)
            return False

    def touch(self, session_id: str) -> None:
        entry = self._active.get(session_id)
        if entry is not None:
            ws, _ = entry
            self._active[session_id] = (ws, time.time())

    def count(self) -> int:
        return len(self._active)

    def purge_stale(self, max_idle_s: float = 120.0) -> int:
        now = time.time()
        stale = [sid for sid, (_ws, ts) in self._active.items() if (now - ts) > max_idle_s]
        for sid in stale:
            self.disconnect(sid)
        return len(stale)

    def ws_for(self, session_id: str) -> Optional[WebSocket]:
        entry = self._active.get(session_id)
        if entry is None:
            return None
        return entry[0]


manager = ConnectionManager()
