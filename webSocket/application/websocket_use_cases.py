# from webSocket.application.notification_service import NotificationService
from ..application.notification_service import NotificationService

class WebSocketUseCases:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service

    async def handle_event(self, raw_data: str):
        notification = notification.from_raw(raw_data)
        await self.notification_service.notify_clients(notification)