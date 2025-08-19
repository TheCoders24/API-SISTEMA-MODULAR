from ..infrastructure.websocket.manager import WebSocketManager
from ..models.notification import Notification


class NotificationService:
    def __init__(self, ws_manager: WebSocketManager):
        self.ws_manager = ws_manager

    async def notify_clients(self, notification: Notification):
        await self.ws_manager.broadcast(
            channel=notification.event_type,
            message=notification.payload
        )