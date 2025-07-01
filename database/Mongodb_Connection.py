from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "sessionDB")

client = AsyncIOMotorClient(MONGO_URL)
mongo_db = client[MONGO_DB]

# Para verificar conexión (async):
async def check_mongo_connection():
    try:
        await client.admin.command("ping")
        print("Conexion a MongoDB establecida para API Keys (async)")
    except Exception as e:
        print(f"Error en conexion async a MongoDB: {e}")
        raise
