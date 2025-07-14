
from ..infraestructura.categoria_repository import CategoriaRepository

class CategoriaService:
    def __init__(self, categoria_repository: CategoriaRepository):
        self.categoria_repository = categoria_repository

    async def obtener_categoria(self):
        return await self.categoria_repository.listar_categorias()
    
    async def obtener_todas_categorias(self):
        return await self.repository.listar_categorias()
    
    async def obtener_categoria(self, categoria_id: int):
        return await self.repository.obtener_por_id(categoria_id)
    