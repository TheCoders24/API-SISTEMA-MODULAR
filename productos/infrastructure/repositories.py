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


    async def update(self, product_id: int, data: dict) -> Optional[dict]:
        try:
            # Construir la consulta UPDATE dinámicamente
            set_clauses = []
            params = {"product_id": product_id}
            
            for key, value in data.items():
                if value is not None:  # Solo actualizar campos con valores no nulos
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = value
            
            if not set_clauses:
                return None  # No hay campos para actualizar
                
            query = f"""
                UPDATE productos 
                SET {', '.join(set_clauses)}
                WHERE id = :product_id
                RETURNING *
            """
            
            result = await self.db.execute(sa.text(query), params)
            await self.db.commit()
            
            updated_product = result.fetchone()
            return dict(updated_product._mapping) if updated_product else None
            
        except Exception as e:
            logging.error(f"Error al actualizar el producto: {str(e)}")
            await self.db.rollback()
            raise e