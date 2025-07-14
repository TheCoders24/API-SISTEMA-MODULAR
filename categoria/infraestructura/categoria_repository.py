# infraestructure/repository/category_repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..domain.models import Categoria

class CategoriaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def listar_categorias(self):
        result = await self.session.execute(select(Categoria))
        return result.scalars().all()
    
    async def obtener_categoria_id(self, categoria: int):
        result = await self.session.execute(
        select(Categoria).where(Categoria.id == id))
        return result.scalar_one_or_none()
    
    async def crear_categoria(self, categoria_data: dict):
        nueva_categoria = Categoria(**categoria_data)
        self.session.add(nueva_categoria)
        await self.session.commit()
        await self.session.refresh(nueva_categoria)
        return nueva_categoria
    
