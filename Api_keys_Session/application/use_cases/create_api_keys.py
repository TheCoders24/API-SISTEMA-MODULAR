from datetime import datetime, timedelta
import secrets
import hashlib
from typing import Dict, Any

#from domain.entities.api_key import APIKeyEntity
#from domain.repositories.api_key_repository import APIKeyRepository
from domain.entities.api_keys import APIKeyEntity
from domain.entities.repositories.api_keys_repository import APIKeyRepository


class CreateAPIKeyUseCase:
    def __init__(self, api_key_repository: APIKeyRepository):
        self.api_key_repository = api_key_repository
    
    def generate_key(self) -> str:
        return secrets.token_urlsafe(32)
    
    def hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
    
    async def execute(
        self,
        user_id: str,
        permissions: list = None,
        expires_in_days: int = 30,
        name: str = None,
        description: str = None
    ) -> Dict[str, Any]:
        raw_key = self.generate_key()
        hashed_key = self.hash_key(raw_key)
        
        api_key_entity = APIKeyEntity(
            id=None,
            user_id=user_id,
            hashed_key=hashed_key,
            permissions=permissions or ["default"],
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            is_active=True,
            name=name,
            description=description
        )
        
        saved_entity = await self.api_key_repository.create(api_key_entity)
        
        return {
            "key_id": saved_entity.id,
            "raw_key": raw_key,
            "expires_at": saved_entity.expires_at
        }