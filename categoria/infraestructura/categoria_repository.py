# infraestructure/repository/category_repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..domain.models import Categoria

class CategoriaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def listar_categorias(self):
        result = await self.session.execute(select(Categoria))
        return result.scalar().all()