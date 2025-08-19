class Notification:
    def __init__(self, event_type: str, playload: dict):
        self.event_type = event_type
        self.payload = playload # valdamos seguna las reglas de negocio
