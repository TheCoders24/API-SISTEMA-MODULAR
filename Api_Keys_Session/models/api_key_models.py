from datetime import datetime, timedelta
from ...database.Mongodb_Connection import mongo_db
from bson.objectid import ObjectId
import hashlib
import secrets

class APIKey:
    def __init__(self):
        self.collection = mongo_db["api_keys"]
    
    def generate_key(self):
        return secrets.token_urlsafe(32)
    
    def hash_key(self, key: str): 
        return hashlib.sha256(key.encode()).hexdigest()
    
    async def create_key(self, user_id: str, permissions: list = None, expires_in_days: int = 30):
        raw_key = self.generate_key()
        hashed_key = self.hash_key(raw_key)
        
        key_data = {
            "user_id": user_id,
            "hashed_key": hashed_key,
            "permissions": permissions or ["default"],
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=expires_in_days),
            "is_active": True
        }
        print("KEY DATA CREATE_KEY", key_data)

        result = await self.collection.insert_one(key_data)
        
        print("RESULT DE KEY_DATA", result)

        return {"key_id": str(result.inserted_id), "raw_key": raw_key}
    
    async def validate_key(self, key: str):
        hashed_key = self.hash_key(key)
        key_data = await self.collection.find_one({
            "hashed_key": hashed_key,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        return key_data

# Fuera de la clase, instancia única para reusar
api_key_manager = APIKey()

# Wrappers para importar funciones directas
async def create_key(user_id: str, permissions: list = None, expires_in_days: int = 30):
    return await api_key_manager.create_key(user_id, permissions, expires_in_days)

async def validate_key(key: str):
    return await api_key_manager.validate_key(key)