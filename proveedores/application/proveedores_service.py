from ..infrastructure.proveedores_repository import PorveedoresRepository

class ProveedoresService:
    def __init__(self, Proveedores_Repository: PorveedoresRepository):
        self.proveedores_repository = Proveedores_Repository

    async def obtener_proveedores(self, skip: int = 0, limit: int = 100):
        return await self.proveedores_repository.listar_proveedores(skip=skip, limit=limit)