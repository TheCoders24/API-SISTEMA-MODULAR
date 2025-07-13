from ..infraestructura.categoria_repository import CategoriaRepository

class CategoriaService:
    def __init__(self, categoria_repository: CategoriaRepository):
        self.categoria_repository = categoria_repository

    async def obtener_categoria(self):
        return await self.categoria_repository.listar_categorias()