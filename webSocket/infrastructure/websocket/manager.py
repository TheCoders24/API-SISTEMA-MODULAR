class WebSocketManager:
    async def broadcast(self, channel: str, message: str):
        for ws in self.active_connections[channel]:
            await ws.send_text(message)