import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
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
    
    async def get_by_id(self, id: int):
        result = await self.db.execute(
            sa.text("SELECT * FROM productos WHERE id = :id"),
            {"id": id}
        )
        return result.fetchone()
    

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