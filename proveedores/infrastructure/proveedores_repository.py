from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..domain.models import Proveedores


class PorveedoresRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def listar_proveedores(self, skip: int = 0, limit: int = 100):
        result = await self.session.execute(
            select(Proveedores).offset(skip).limit(limit)
        )
        return result.scalars().all()