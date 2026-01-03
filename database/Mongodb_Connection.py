import logging
from motor.motor_asyncio import AsyncIOMotorClient
# from beanie import init_beanie # Opcional pero recomendado para esquemas
import os

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.db = None
        self.url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB", "sessionDB")

    async def connect(self):
        """Inicializa la conexión con parámetros de optimización."""
        try:
            # Configuración avanzada: Pool de conexiones y timeouts
            self.client = AsyncIOMotorClient(
                self.url,
                maxPoolSize=50,       # Límite de conexiones para evitar saturar RAM
                minPoolSize=10,       # Mantener conexiones calientes
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[self.db_name]
            
            # Verificar con un ping
            await self.client.admin.command("ping")
            logger.info("✅ Conexión a MongoDB establecida")
        except Exception as e:
            logger.error(f"❌ Error conectando a MongoDB: {e}")
            raise

    async def close(self):
        """Cierra el cliente al apagar la aplicación."""
        if self.client:
            self.client.close()
            logger.info("🔌 Conexión a MongoDB cerrada")

# Instancia única (Singleton) para ser usada en toda la app
mongo_manager = MongoDBManager()

# Dependencia para FastAPI
async def get_mongo_db():
    return mongo_manager.db