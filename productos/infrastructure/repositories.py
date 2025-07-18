from typing import Optional, List
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from ...productos.models.models import Producto 

class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, product_id: int) -> Optional[Producto]:
        result = await self.db.execute(sa.select(Producto).where(Producto.id == product_id))
        return result.scalar_one_or_none()
    
    async def get_by_name(self, nombre: str):
        result = await self.db.execute(
            sa.text("SELECT * FROM productos WHERE nombre = :nombre"),
            {"nombre": nombre}
        )
        return result.fetchone()
    
    async def create(self, data: dict):
        result = await self.db.execute(
            sa.text("""
                INSERT INTO productos (nombre, descripcion, precio, stock, categoria_id, proveedor_id)
                VALUES (:nombre, :descripcion, :precio, :stock, :categoria_id, :proveedor_id)
                RETURNING *
            """),
            data
        )
        return result.fetchone()
    
    async def obtener_todos_productos(self) -> List[dict]:
        try:
            result = await self.db.execute(sa.text("SELECT * FROM productos"))
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            logging.error(f"Error al obtener productos: {str(e)}")
            raise Exception(f"Error al obtener productos: {str(e)}")
        
    async def delete(self, id: int) -> bool:
        try:
            product = await self.db.get(Producto, id)
            if not product:
                return False
            await self.db.delete(product)
            await self.db.commit()
            return True
        except Exception as e:
            logging.error(f"Error al eliminar el producto: {str(e)}")
            await self.db.rollback()
            return False
