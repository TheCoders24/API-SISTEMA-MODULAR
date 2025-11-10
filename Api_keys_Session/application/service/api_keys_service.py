import asyncio
from typing import List, Optional, Dict, Any

#from domain.repositories.api_key_repository import APIKeyRepository
#from application.use_cases.create_api_key import CreateAPIKeyUseCase
#from application.use_cases.validate_api_key import ValidateAPIKeyUseCase

from domain.entities.repositories.api_keys_repository import APIKeyRepository
from application.use_cases.create_api_keys import CreateAPIKeyUseCase
from application.use_cases.validate_api_keys import ValidateAPIKeyUseCase

class APIKeyService:
    def __init__(self, api_key_repository: APIKeyRepository):
        self.repository = api_key_repository
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Inicia la tarea automática de limpieza"""
        async def cleanup_loop():
            while True:
                try:
                    await self.repository.delete_expired()
                    await asyncio.sleep(3600)  # Cada hora
                except Exception as e:
                    print(f"Error en limpieza automática: {e}")
                    await asyncio.sleep(300)
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def stop_cleanup(self):
        """Detiene la limpieza automática"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
    
    async def create_key(
        self,
        user_id: str,
        permissions: List[str] = None,
        expires_in_days: int = 30,
        name: str = None,
        description: str = None
    ) -> Dict[str, Any]:
        use_case = CreateAPIKeyUseCase(self.repository)
        return await use_case.execute(user_id, permissions, expires_in_days, name, description)
    
    async def validate_key(self, key: str) -> Optional[Dict[str, Any]]:
        use_case = ValidateAPIKeyUseCase(self.repository)
        return await use_case.execute(key)
    
    async def get_user_keys(self, user_id: str) -> List[Dict[str, Any]]:
        entities = await self.repository.find_by_user_id(user_id)
        return [self._entity_to_dict(entity) for entity in entities]
    
    async def force_cleanup(self) -> int:
        """Fuerza limpieza inmediata"""
        return await self.repository.delete_expired()
    
    async def get_stats(self) -> Dict[str, Any]:
        return await self.repository.get_stats()
    
    def _entity_to_dict(self, entity) -> Dict[str, Any]:
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