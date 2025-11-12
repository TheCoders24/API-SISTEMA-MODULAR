from datetime import datetime
import hashlib
from typing import Optional, Dict, Any
# from domain.repositories.api_key_repository import APIKeyRepository
from ...domain.entities.repositories.api_keys_repository import APIKeyRepository

class ValidateAPIKeyUseCase:
    def __init__(self, api_key_repository: APIKeyRepository):
        self.api_key_repository = api_key_repository
    
    def hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
    
    async def execute(self, key: str) -> Optional[Dict[str, Any]]:
        hashed_key = self.hash_key(key)
        entity = await self.api_key_repository.find_by_hashed_key(hashed_key)
        
        if not entity or not entity.is_valid():
            return None
        
        # Actualizar last_used
        entity.last_used = datetime.utcnow()
        await self.api_key_repository.update(entity)
        
        return {
            "id": entity.id,
            "user_id": entity.user_id,
            "permissions": entity.permissions,
            "created_at": entity.created_at,
            "expires_at": entity.expires_at,
            "is_active": entity.is_active,
            "last_used": entity.last_used,
            "name": entity.name,
            "description": entity.description
        }