from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class APIKeyCreate(BaseModel):
    user_id: str = Field(..., description="ID del usuario")
    permissions: List[str] = Field(default=["default"])
    expires_in_days: int = Field(default=30, ge=1, le=365)
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class APIKeyResponse(BaseModel):
    key_id: str
    raw_key: str
    expires_at: datetime

class APIKeyInfo(BaseModel):
    id: str
    user_id: str
    permissions: List[str]
    created_at: datetime
    expires_at: datetime
    is_active: bool
    last_used: Optional[datetime]
    name: Optional[str]
    description: Optional[str]