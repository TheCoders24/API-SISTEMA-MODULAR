from sqlalchemy.ext.asyncio import AsyncSession
from .models import Producto
from sqlalchemy.orm import Session
from . import models, schemas

async def Crear_Productos(db: AsyncSession, producto: schemas.ProductoCreate):
    db_producto = Producto(**producto.dict())
    db.add(db_producto)
    await db.commit()
    await db.refresh()
    return db_producto

def Obtener_Productos(db: Session, producto_id: int):
    return db.query(models.Producto).filter(models.Producto.id == producto_id).first()


def Actualizar_Stock(db: Session, producto_id: int, nuevo_stock: int):
    db_producto = db.query(models.Producto).filter(models.Producto.id == producto_id).first()
    if db_producto:
        db_producto.stock = nuevo_stock
        db.commit()
        db.refresh(db_producto)
        return db_producto