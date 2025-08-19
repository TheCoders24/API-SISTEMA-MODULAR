from pydantic import BaseModel


class WSMessageSchema(BaseModel):
    channel: str
    content: str