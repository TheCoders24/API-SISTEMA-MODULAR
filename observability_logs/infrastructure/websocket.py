from fastapi import WebSocket
from typing import Dict, List, Optional
from enum import Enum
import json
from datetime import datetime
import asyncio


class SubscriptionType(str, Enum):
    ALL = "all"
    SECURITY = "security"
    CRITICAL = "critical"
    USER = "user"
    TRACE = "trace"


class WebSocketPublisher:
    """Manejador de conexiones WebSocket para logs en vivo"""

    def __init__(self):
        self.all_connections: List[WebSocket] = []
        self.security_connections: List[WebSocket] = []
        self.critical_connections: List[WebSocket] = []
        self.user_subscriptions: Dict[str, List[WebSocket]] = {}
        self.trace_subscriptions: Dict[str, List[WebSocket]] = {}

        # 🔒 Lock async para evitar race conditions
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        sub_type: SubscriptionType,
        filter_value: Optional[str] = None
    ):
        await websocket.accept()

        async with self._lock:
            if sub_type == SubscriptionType.ALL:
                self.all_connections.append(websocket)

            elif sub_type == SubscriptionType.SECURITY:
                self.security_connections.append(websocket)

            elif sub_type == SubscriptionType.CRITICAL:
                self.critical_connections.append(websocket)

            elif sub_type == SubscriptionType.USER and filter_value:
                self.user_subscriptions.setdefault(filter_value, []).append(websocket)

            elif sub_type == SubscriptionType.TRACE and filter_value:
                self.trace_subscriptions.setdefault(filter_value, []).append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            for collection in (
                self.all_connections,
                self.security_connections,
                self.critical_connections,
            ):
                if websocket in collection:
                    collection.remove(websocket)

            for mapping in (self.user_subscriptions, self.trace_subscriptions):
                for key in list(mapping.keys()):
                    if websocket in mapping[key]:
                        mapping[key].remove(websocket)
                    if not mapping[key]:
                        del mapping[key]

    async def publish(self, log_entry):
        # Convertir a dict
        log_data = (
            log_entry.__dict__.copy()
            if hasattr(log_entry, "__dict__")
            else dict(log_entry)
        )

        if isinstance(log_data.get("timestamp"), datetime):
            log_data["timestamp"] = log_data["timestamp"].isoformat()

        message = json.dumps(log_data, default=str)

        async def _safe_send(connections: List[WebSocket]):
            disconnected = []
            for ws in connections:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.append(ws)

            for ws in disconnected:
                await self.disconnect(ws)

        # ALL
        await _safe_send(self.all_connections)

        # SECURITY
        if log_data.get("category") == "security":
            await _safe_send(self.security_connections)

        # CRITICAL
        if log_data.get("level") in {"critical", "error"}:
            await _safe_send(self.critical_connections)

        # USER
        user_id = log_data.get("user_id")
        if user_id and user_id in self.user_subscriptions:
            await _safe_send(self.user_subscriptions[user_id])

        # TRACE
        trace_id = log_data.get("trace_id")
        if trace_id and trace_id in self.trace_subscriptions:
            await _safe_send(self.trace_subscriptions[trace_id])
