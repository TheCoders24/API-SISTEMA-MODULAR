from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URI_APIKEYS")
MONGO_DB = os.getenv("MONGODB_URL_DATABASE")

try:
    mongo_client = MongoClient(MONGO_URL)
    mongo_db = mongo_client[MONGO_DB]
    # Verificamos la Conexion de MongoDB
    mongo_client.admin.command('ping')
    print("Conexion a MongoDB Establecida para API Keys")
except ConnectionFailure as e:
    print(f"Error de Conexion a MongoDB: {e}")
    raise