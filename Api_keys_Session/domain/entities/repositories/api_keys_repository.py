from abc import ABC, abstractmethod
from typing import List, Optional
#from domain.entities.api_keys import  APIKeyEntity
from ...entities.api_keys import APIKeyEntity
class APIKeyRepository(ABC):
    """Interface del repositorio de API Keys"""
    
    @abstractmethod
    async def create(self, api_key: APIKeyEntity) -> APIKeyEntity:
        pass
    
    @abstractmethod
    async def find_by_hashed_key(self, hashed_key: str) -> Optional[APIKeyEntity]:
        pass
    
    @abstractmethod
    async def find_by_id(self, key_id: str) -> Optional[APIKeyEntity]:
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[APIKeyEntity]:
        pass
    
    @abstractmethod
    async def update(self, api_key: APIKeyEntity) -> bool:
        pass
    
    @abstractmethod
    async def delete_expired(self) -> int:
        pass
    
    @abstractmethod
    async def get_stats(self) -> dict:
        pass