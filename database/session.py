from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Formato: postgresql+asyncpg://usuario:contraseña@host:puerto/nombre_bd
DATABASE_URL = "postgresql+asyncpg://postgres:12345@localhost:5432/inventario_db"

engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session