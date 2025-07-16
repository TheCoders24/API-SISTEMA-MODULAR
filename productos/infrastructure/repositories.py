from typing import Optional
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from ...productos.presentation.schemas import Producto

class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, product_id: int):
        """Obtiene un producto por ID"""
        result = await self.db.execute(  # Debe ser self.db no self.session
            sa.select(Producto).where(Producto.id == product_id)
        )
        return result.scalar_one_or_none()
    
    async def delete(self, product: Producto) -> None:
        """Elimina un producto existente"""
        await self.db.delete(product)


    async def get_by_name(self, nombre: str):
        result = await self.db.execute(
            sa.text("SELECT id FROM productos WHERE nombre = :nombre"),
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
    
    async def get_by_id(self, product_id: int) -> Optional[Producto]:
        """Obtiene un producto usando el modelo SQLAlchemy"""
        return await self.db.get(Producto, product_id)

    async def get_by_nombre(self, nombre: str):
        result = await self.db.execute(
            sa.text("SELECT * FROM productos WHERE nombre = :nombre"),
            {"nombre": nombre}
        )
        return result.fetchone()

    async def obtener_todos_productos(self) -> list[dict]:
        """Obtiene todos los productos disponibles"""
        try:
            result = await self.db.execute(sa.text("SELECT * FROM productos"))
            rows = result.fetchall()  
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            raise  Exception(f"Error al  Obtener Productos", {str(e)})
        
    async def delete(self, id: int) -> bool:
        """Elimina un producto usando el modelo SQLAlchemy correcto"""
        try:
            product = await self.db.get(Producto, id)
            if product:
                await self.db.delete(product)
                await self.db.flush()
                return True
            return True
        except Exception as e:
            logging.error(f"Error al Eliminar el Producto {str(e)}")
            await self.db.rollback()
            return False