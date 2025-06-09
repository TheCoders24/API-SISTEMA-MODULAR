# Database/ UnitOfWork

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

class UnitOfWork:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def transaction(self):
        try:
            yield
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        finally:
            await self.db.close()
            