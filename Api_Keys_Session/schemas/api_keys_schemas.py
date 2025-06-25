from pydantic import BaseModel
from datetime import datetime

class APIkeyCreate(BaseModel):
    user_id: str
    permissions: list = ["default"]
    expires_in_days: int = 30

class APIkeyResponse(BaseModel):
    key_id: str
    raw_key: str

class APIkeyInfo(BaseModel):
    user_id: str
    permission: list
    create_at: datetime
    expire_at: datetime
    is_active: bool