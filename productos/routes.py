from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.session import get_db
from . import schemas
import sqlalchemy as sa  # Para SQL directo

router = APIRouter(prefix="/productos", tags=["productos"])

@router.post("/", response_model=schemas.Producto)
async def crear_producto(
    producto: schemas.ProductoCreate, 
    db: AsyncSession = Depends(get_db)
):
    # Consulta SQL directa (ajusta 'productos' al nombre exacto de tu tabla)
    result = await db.execute(
        sa.text("""
        INSERT INTO productos (nombre, precio, stock) 
        VALUES (:nombre, :precio, :stock) 
        RETURNING *
        """),
        producto.dict()
    )
    await db.commit()
    return result.fetchone()

@router.get("/{producto_id}", response_model=schemas.Producto)
async def leer_producto(
    producto_id: int, 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        sa.text("SELECT * FROM productos WHERE id = :id"),
        {"id": producto_id}
    )
    producto = result.fetchone()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.put("/{producto_id}/stock", response_model=schemas.Producto)
async def actualizar_stock(
    producto_id: int, 
    stock: int, 
    db: AsyncSession = Depends(get_db)
):
    # Verifica que el producto existe primero
    await leer_producto(producto_id, db)  # Reutiliza la función existente
    
    await db.execute(
        sa.text("""
        UPDATE productos 
        SET stock = :stock 
        WHERE id = :id 
        RETURNING *
        """),
        {"id": producto_id, "stock": stock}
    )
    await db.commit()
    return (await db.execute(
        sa.text("SELECT * FROM productos WHERE id = :id"),
        {"id": producto_id}
    )).fetchone()