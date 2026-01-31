# database/session.py
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:12345@localhost:5432/db_sistema_inventario_version2")

# Motor optimizado para alta concurrencia
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Conexiones simultáneas
    max_overflow=10,        # Margen de seguridad
    pool_pre_ping=True,     # Evita "conexiones fantasma"
    echo=False              # Cambia a True solo para debuggear SQL
)

# Fábrica de sesiones
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Dependencia para FastAPI
async def get_db():
    async with async_session() as session:
        yield session



"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Cargar variables de entorno (opcional)
load_dotenv()

# URL de conexión a PostgreSQL
DATABASE_URL = "postgresql+asyncpg://postgres:12345@localhost:5432/db_sistema_inventario_version2"
DATABASE = os.getenv("DATABASE_URL")

# Crear el motor asíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Crear sessionmaker asíncrono (¡usa async_sessionmaker mejor que sessionmaker!)
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependencia para usar en FastAPI
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
"""
