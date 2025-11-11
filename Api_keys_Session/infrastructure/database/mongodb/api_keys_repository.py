from datetime import datetime
from typing import List, Optional
from bson import ObjectId
import hashlib
import secrets
from domain.entities.api_keys import APIKeyEntity
from ....domain.entities.repositories.api_keys_repository import APIKeyRepository
from .....database.Mongodb_Connection import mongo_db


class MongoDBAPIKeyRepository(APIKeyRepository):
    """Implementación concreta del repositorio usando MongoDB"""
    
    def __init__(self):
        self.collection = mongo_db["api_keys"]
    
    def _to_entity(self, data: dict) -> Optional[APIKeyEntity]:
        if not data:
            return None
        return APIKeyEntity(
            id=str(data["_id"]),
            user_id=data["user_id"],
            hashed_key=data["hashed_key"],
            permissions=data["permissions"],
            created_at=data["created_at"],
            expires_at=data["expires_at"],
            is_active=data["is_active"],
            last_used=data.get("last_used"),
            name=data.get("name"),
            description=data.get("description")
        )
    
    def _to_document(self, entity: APIKeyEntity) -> dict:
        return {
            "user_id": entity.user_id,
            "hashed_key": entity.hashed_key,
            "permissions": entity.permissions,
            "created_at": entity.created_at,
            "expires_at": entity.expires_at,
            "is_active": entity.is_active,
            "last_used": entity.last_used,
            "name": entity.name,
            "description": entity.description
        }
    
    async def create(self, api_key: APIKeyEntity) -> APIKeyEntity:
        document = self._to_document(api_key)
        result = await self.collection.insert_one(document)
        api_key.id = str(result.inserted_id)
        return api_key
    
    async def find_by_hashed_key(self, hashed_key: str) -> Optional[APIKeyEntity]:
        doc = await self.collection.find_one({"hashed_key": hashed_key})
        return self._to_entity(doc)
    
    async def find_by_id(self, key_id: str) -> Optional[APIKeyEntity]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(key_id)})
            return self._to_entity(doc)
        except:
            return None
    
    async def find_by_user_id(self, user_id: str) -> List[APIKeyEntity]:
        cursor = self.collection.find({"user_id": user_id})
        entities = []
        async for doc in cursor:
            entity = self._to_entity(doc)
            if entity:
                entities.append(entity)
        return entities
    
    async def update(self, api_key: APIKeyEntity) -> bool:
        try:
            document = self._to_document(api_key)
            result = await self.collection.update_one(
                {"_id": ObjectId(api_key.id)},
                {"$set": document}
            )
            return result.modified_count > 0
        except:
            return False
    
    async def delete_expired(self) -> int:
        result = await self.collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        return result.deleted_count
    
    async def get_stats(self) -> dict:
        total = await self.collection.count_documents({})
        active = await self.collection.count_documents({"is_active": True})
        expired = await self.collection.count_documents({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        
        return {
            "total_keys": total,
            "active_keys": active,
            "expired_keys": expired
        }