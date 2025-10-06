from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from ..domain.models import Proveedores
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class ProveedoresRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def listar_proveedores(self, skip: int = 0, limit: int = 100):
        result = await self.session.execute(
            select(Proveedores).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def obtener_por_id(self, proveedor_id: int):
        result = await self.session.execute(
            select(Proveedores).where(Proveedores.id == proveedor_id)
        )
        return result.scalar_one_or_none()

    async def crear(self, proveedor_data):
        proveedor = Proveedores(**proveedor_data.dict())
        self.session.add(proveedor)
        await self.session.commit()
        await self.session.refresh(proveedor)
        return proveedor

    async def actualizar(self, proveedor_id: int, proveedor_data):
        proveedor = await self.obtener_por_id(proveedor_id)
        if proveedor:
            update_data = proveedor_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(proveedor, field, value)
            await self.session.commit()
            await self.session.refresh(proveedor)
        return proveedor

    async def eliminar(self, proveedor_id: int):
        proveedor = await self.obtener_por_id(proveedor_id)
        if proveedor:
            await self.session.delete(proveedor)
            await self.session.commit()
        return proveedor

    async def existe_proveedor(self, nombre: str):
        result = await self.session.execute(
            select(Proveedores).where(Proveedores.nombre == nombre)
        )
        return result.scalar_one_or_none() is not None

    async def buscar_por_nombre(self, nombre: str):
        result = await self.session.execute(
            select(Proveedores).where(Proveedores.nombre.ilike(f"%{nombre}%"))
        )
        return result.scalars().all()