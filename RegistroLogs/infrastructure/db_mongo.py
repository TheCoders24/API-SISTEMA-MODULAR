from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client.security_db

async def init_mongo():
    # TTL de 90 días para logs históricos
    await db.suspicious_logs.create_index("created_at", expireAfterSeconds=90*24*3600)
