from datetime import datetime, timedelta
import secrets
import hashlib
from typing import Dict, Any, List, Optional
from ...domain.entities.api_keys import APIKeyEntity
from ...domain.entities.repositories.api_keys_repository import APIKeyRepository
from ...presentation.schemas.api_keys_schemas import APIKeyCreate


class CreateAPIKeyUseCase:
    def __init__(self, api_key_repository: APIKeyRepository):
        self.api_key_repository = api_key_repository

    def generate_key(self) -> str:
        """Genera una API key aleatoria"""
        return secrets.token_urlsafe(32)

    def hash_key(self, key: str) -> str:
        """Hashea la API key con SHA256"""
        return hashlib.sha256(key.encode()).hexdigest()

    async def execute(
        self,
        user_id: str,
        permissions: Optional[List[str]] = None,
        expires_in_days: int = 30,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Crea una nueva API Key para el usuario especificado"""
        raw_key = self.generate_key()
        hashed_key = self.hash_key(raw_key)

        api_key_entity = APIKeyEntity(
            id=None,
            user_id=str(user_id),
            hashed_key=hashed_key,
            permissions=permissions or ["default"],
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            is_active=True,
            name=name,
            description=description,
        )

        saved_entity = await self.api_key_repository.create(api_key_entity)

        # 🔧 Manejo flexible: puede ser dict o entidad
        if isinstance(saved_entity, dict):
            key_id = saved_entity.get("id")
            expires_at = saved_entity.get("expires_at")
            permissions = saved_entity.get("permissions", [])
            is_active = saved_entity.get("is_active", True)
        else:
            key_id = getattr(saved_entity, "id", None)
            expires_at = getattr(saved_entity, "expires_at", None)
            permissions = getattr(saved_entity, "permissions", [])
            is_active = getattr(saved_entity, "is_active", True)

        return {
            "key_id": key_id,
            "raw_key": raw_key,
            "expires_at": expires_at,
            "permissions": permissions,
            "is_active": is_active,
        }
