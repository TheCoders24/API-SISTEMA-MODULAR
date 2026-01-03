# from .....database.Mongodb_Connection import mongo_db
from .....database.Mongodb_Connection import mongo_manager
from ....domain.entities.api_keys import APIKeyEntity
from ....domain.entities.repositories.api_keys_repository import APIKeyRepository
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta

class MongoAPIKeyRepository(APIKeyRepository):

    def __init__(self):
        self.collection = mongo_manager.db["api_keys"]

    async def create(self, api_key: APIKeyEntity) -> APIKeyEntity:
        print(f"[DEBUG] Guardando API Key... user_id={api_key.user_id}")
        data = {
            "_id": ObjectId(api_key.id) if api_key.id else ObjectId(),
            "user_id": api_key.user_id,
            "hashed_key": api_key.hashed_key,
            "expires_at": api_key.expires_at,
            "created_at": api_key.created_at,
        }
        print(f"[DEBUG] Datos a insertar en Mongo: {data}")
        await self.collection.insert_one(data)
        api_key.id = str(data["_id"])
        print(f"[DEBUG] API Key almacenada con id: {api_key.id}")
        return api_key

    async def find_by_hashed_key(self, hashed_key: str):
        print(f"[DEBUG] Buscando por hashed_key: {hashed_key}")
        result = await self.collection.find_one({"hashed_key": hashed_key})
        print(f"[DEBUG] Resultado crudo Mongo: {result}")
        return self._map(result) if result else None

    async def find_by_id(self, key_id: str):
        print(f"[DEBUG] Buscando API Key por id: {key_id}")
        result = await self.collection.find_one({"_id": ObjectId(key_id)})
        print(f"[DEBUG] Resultado crudo Mongo: {result}")
        return self._map(result) if result else None

    async def find_by_user_id(self, user_id: str):
        print(f"[DEBUG] Buscando API Keys para user_id: {user_id}")
        cursor = self.collection.find({"user_id": user_id})
        results = await cursor.to_list(length=None)
        print(f"[DEBUG] Se encontraron {len(results)} API Keys")
        return [self._map(doc) for doc in results]

    async def update(self, api_key: APIKeyEntity) -> bool:
        print(f"[DEBUG] Actualizando API Key {api_key.id}")
        result = await self.collection.update_one(
            {"_id": ObjectId(api_key.id)},
            {"$set": {
                "hashed_key": api_key.hashed_key,
                "expires_at": api_key.expires_at,
                "last_used": getattr(api_key, "last_used", None)
            }}
        )
        print(f"[DEBUG] modified_count={result.modified_count}")
        return result.modified_count > 0

    async def delete_expired(self) -> int:
        now = datetime.utcnow()
        print(f"[DEBUG] Eliminando API Keys expiradas antes de {now}")
        result = await self.collection.delete_many({"expires_at": {"$lt": now}})
        print(f"[DEBUG] Total eliminadas: {result.deleted_count}")
        return result.deleted_count

    async def get_stats(self) -> dict:
        total = await self.collection.count_documents({})
        activos = await self.collection.count_documents({"expires_at": {"$gt": datetime.utcnow()}})
        print(f"[DEBUG] Stats -> total: {total}, activos: {activos}")
        return {"total": total, "activos": activos}

    def _map(self, doc) -> APIKeyEntity:
        print(f"[DEBUG] Mapeando documento Mongo a entidad: {doc}")
        if not doc:
            return None
        return APIKeyEntity(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            hashed_key=doc["hashed_key"],
            expires_at=doc["expires_at"],
            created_at=doc["created_at"]
        )
