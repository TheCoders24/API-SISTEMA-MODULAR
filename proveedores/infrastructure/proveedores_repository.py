from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..domain.models import Proveedores


class PorveedoresRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def listar_proveedores(self):
        result = await self.session.execute(select(Proveedores))
        return result.scalars().all()