class WebSocketMessage:
    def __init__(self, channel: str, content: str):
        self.channel = channel
        self.content = content
        