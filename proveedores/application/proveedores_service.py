from ..infrastructure.proveedores_repository import ProveedoresRepository
from ..domain.schemas import ProveedorCreate, ProveedorUpdate
from typing import Optional, List
from fastapi import HTTPException

class ProveedoresService:
    def __init__(self, proveedores_repository: ProveedoresRepository):
        self.proveedores_repository = proveedores_repository

    async def obtener_proveedores(self, skip: int = 0, limit: int = 100):
        return await self.proveedores_repository.listar_proveedores(skip=skip, limit=limit)

    async def obtener_proveedor_por_id(self, proveedor_id: int):
        return await self.proveedores_repository.obtener_por_id(proveedor_id)

    async def crear_proveedor(self, proveedor_data):
        return await self.proveedores_repository.crear(proveedor_data)

    async def actualizar_proveedor(self, proveedor_id: int, proveedor_data):
        return await self.proveedores_repository.actualizar(proveedor_id, proveedor_data)

    async def eliminar_proveedor(self, proveedor_id: int):
        return await self.proveedores_repository.eliminar(proveedor_id)

    async def verificar_proveedor_existente(self, nombre: str):
        return await self.proveedores_repository.existe_proveedor(nombre)

    async def buscar_proveedores_por_nombre(self, nombre: str):
        return await self.proveedores_repository.buscar_por_nombre(nombre)