from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class APIKeyEntity:
    """IEntidad de dominio para AP Keys"""
    id: Optional[str]
    user_id: str
    hashed_key: str
    permissions: List[str]
    created_at: datetime
    expires_at: datetime
    is_active: bool
    last_used: Optional[datetime] = None
    name: Optional[str] = None
    description: Optional[str] = None
    
    def is_expired(self) -> bool:
        return self.expires_at < datetime.utcnow()
    
    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired()