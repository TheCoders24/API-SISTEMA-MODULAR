# from ..database.mongo_connection import mongo_db
# from ...domain.entities.api_keys import APIKeyEntity
# from ...domain.repositories.api_keys_repository import APIKeyRepository
# from bson import ObjectId

from .....database.Mongodb_Connection import mongo_db
from ....domain.entities.api_keys import APIKeyEntity
from ....domain.entities.repositories.api_keys_repository import APIKeyRepository
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta


class MongoAPIKeyRepository(APIKeyRepository):
    """Implementación del repositorio de API Keys usando MongoDB y Motor"""

    def __init__(self):
        self.collection = mongo_db["api_keys"]

    async def create(self, api_key: APIKeyEntity) -> APIKeyEntity:
        """Guarda una API Key en MongoDB"""
        # Convertir entidad a dict manualmente
        data = {
            "_id": ObjectId(api_key.id) if api_key.id else ObjectId(),
            "user_id": api_key.user_id,
            "hashed_key": api_key.hashed_key,
            "expires_at": api_key.expires_at,
            "created_at": api_key.created_at,
        }
        await self.collection.insert_one(data)
        api_key.id = str(data["_id"])
        return api_key

    async def find_by_hashed_key(self, hashed_key: str):
        result = await self.collection.find_one({"hashed_key": hashed_key})
        return self._map(result) if result else None

    async def find_by_id(self, key_id: str):
        result = await self.collection.find_one({"_id": ObjectId(key_id)})
        return self._map(result) if result else None

    async def find_by_user_id(self, user_id: str):
        cursor = self.collection.find({"user_id": user_id})
        results = await cursor.to_list(length=None)
        return [self._map(doc) for doc in results]

    async def update(self, api_key: APIKeyEntity) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(api_key.id)},
            {"$set": {
                "hashed_key": api_key.hashed_key,
                "expires_at": api_key.expires_at
            }}
        )
        return result.modified_count > 0

    async def delete_expired(self) -> int:
        now = datetime.utcnow()
        result = await self.collection.delete_many({"expires_at": {"$lt": now}})
        return result.deleted_count

    async def get_stats(self) -> dict:
        total = await self.collection.count_documents({})
        activos = await self.collection.count_documents({"expires_at": {"$gt": datetime.utcnow()}})
        return {"total": total, "activos": activos}

    # ------------------------------------------------------------
    # Función auxiliar para mapear documentos a entidades
    # ------------------------------------------------------------
    def _map(self, doc) -> APIKeyEntity:
        if not doc:
            return None
        return APIKeyEntity(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            hashed_key=doc["hashed_key"],
            expires_at=doc["expires_at"],
            created_at=doc["created_at"]
        )
