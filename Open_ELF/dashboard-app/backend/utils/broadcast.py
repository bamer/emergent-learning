"""
WebSocket broadcast management for the Emergent Learning Dashboard.

Provides ConnectionManager for handling real-time updates to connected clients.
"""

import asyncio

from datetime import datetime
from typing import List

from fastapi import WebSocket

# Import centralized logger (NOUVEAU SYSTÈME UNIFIÉ)
try:
    from Open_ELF.utils.elf_logging import get_logger, log_critical, log_error, log_warning, log_info

    logger = get_logger("broadcast")
except ImportError:
    import logging

    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("broadcast")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.last_state_hash = None
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        async with self._lock:
            connections = list(self.active_connections)

        dead_connections = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast to client: {e}")
                dead_connections.append(connection)

        if dead_connections:
            async with self._lock:
                for conn in dead_connections:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)

    async def broadcast_update(self, update_type: str, data: dict):
        await self.broadcast(
            {"type": update_type, "timestamp": datetime.now().isoformat(), "data": data}
        )
