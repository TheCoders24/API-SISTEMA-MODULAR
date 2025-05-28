from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Carga de variables de entorno si las usas
# load_dotenv()

DATABASE_URL = "postgresql+asyncpg://postgres:12345@localhost:5432/sistemainventario"
# DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el motor asíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Crear sesión asíncrona
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency para FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session  # Se cierra automáticamente al salir del contexto
