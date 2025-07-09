from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

class UnitOfWork:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @asynccontextmanager
    async def transaction(self):
        try:
            await self.db.begin()  # Inicia la transacción
            yield
            await self.db.commit()  # Commit si no hay error
        except Exception:
            await self.db.rollback()  # Rollback si hay error
            raise
        finally:
            await self.db.close()  # Cierra la sesión
