from datetime import datetime
from typing import List, Optional
from bson import ObjectId
import hashlib
import secrets
from ....domain.entities.api_keys import APIKeyEntity
from ....domain.entities.repositories.api_keys_repository import APIKeyRepository
from .....database.Mongodb_Connection import mongo_manager


class MongoDBAPIKeyRepository(APIKeyRepository):
    """Implementación concreta del repositorio usando MongoDB"""
    
    def __init__(self):
        print("[DEBUG][INIT] Conectando a la colección 'api_keys'")
        self.collection = mongo_manager.db["api_keys"]
    
    def _to_entity(self, data: dict) -> Optional[APIKeyEntity]:
        print(f"[DEBUG][_to_entity] Raw Mongo data: {data}")
        if not data:
            print("[DEBUG][_to_entity] No data received.")
            return None
        
        entity = APIKeyEntity(
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
        print(f"[DEBUG][_to_entity] Converted to entity: {entity}")
        return entity
    
    def _to_document(self, entity: APIKeyEntity) -> dict:
        document = {
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
        print(f"[DEBUG][_to_document] Entity -> Document: {document}")
        return document
    
    async def create(self, api_key: APIKeyEntity) -> APIKeyEntity:
        print(f"[DEBUG][CREATE] Creating API Key for user_id={api_key.user_id}")
        document = self._to_document(api_key)
        result = await self.collection.insert_one(document)
        api_key.id = str(result.inserted_id)
        print(f"[DEBUG][CREATE] API Key inserted with id={api_key.id}")
        return api_key
    
    async def find_by_hashed_key(self, hashed_key: str) -> Optional[APIKeyEntity]:
        print(f"[DEBUG][find_by_hashed_key] Searching by hashed_key={hashed_key}")
        doc = await self.collection.find_one({"hashed_key": hashed_key})
        print(f"[DEBUG][find_by_hashed_key] Raw result: {doc}")
        return self._to_entity(doc)
    
    async def find_by_id(self, key_id: str) -> Optional[APIKeyEntity]:
        print(f"[DEBUG][find_by_id] Searching by ID={key_id}")
        try:
            doc = await self.collection.find_one({"_id": ObjectId(key_id)})
            print(f"[DEBUG][find_by_id] Raw result: {doc}")
            return self._to_entity(doc)
        except Exception as e:
            print(f"[DEBUG][find_by_id] ERROR: {e}")
            return None
    
    async def find_by_user_id(self, user_id: str) -> List[APIKeyEntity]:
        print(f"[DEBUG][find_by_user_id] Searching keys for user_id={user_id}")
        cursor = self.collection.find({"user_id": user_id})
        entities = []
        async for doc in cursor:
            print(f"[DEBUG][find_by_user_id] Raw document: {doc}")
            entity = self._to_entity(doc)
            if entity:
                entities.append(entity)
        print(f"[DEBUG][find_by_user_id] Found {len(entities)} keys")
        return entities
    
    async def update(self, api_key: APIKeyEntity) -> bool:
        print(f"[DEBUG][UPDATE] Updating API Key id={api_key.id}")
        try:
            document = self._to_document(api_key)
            print(f"[DEBUG][UPDATE] Document to update: {document}")
            result = await self.collection.update_one(
                {"_id": ObjectId(api_key.id)},
                {"$set": document}
            )
            print(f"[DEBUG][UPDATE] modified_count={result.modified_count}")
            return result.modified_count > 0
        except Exception as e:
            print(f"[DEBUG][UPDATE] ERROR: {e}")
            return False
    
    async def delete_expired(self) -> int:
        now = datetime.utcnow()
        print(f"[DEBUG][delete_expired] Deleting keys expired before {now}")
        result = await self.collection.delete_many({
            "expires_at": {"$lt": now}
        })
        print(f"[DEBUG][delete_expired] Deleted: {result.deleted_count}")
        return result.deleted_count
    
    async def get_stats(self) -> dict:
        print("[DEBUG][get_stats] Fetching statistics")
        total = await self.collection.count_documents({})
        active = await self.collection.count_documents({"is_active": True})
        expired = await self.collection.count_documents({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        
        stats = {
            "total_keys": total,
            "active_keys": active,
            "expired_keys": expired
        }
        print(f"[DEBUG][get_stats] Stats: {stats}")
        return stats
