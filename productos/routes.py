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
    # Consulta SQL corregida con todos los parámetros
    result = await db.execute(
        sa.text("""
        INSERT INTO productos (
            nombre, 
            descripcion, 
            precio, 
            stock, 
            categoria_id, 
            proveedor_id, 
            usuario_id
        ) 
        VALUES (
            :nombre, 
            :descripcion, 
            :precio, 
            :stock, 
            :categoria_id, 
            :proveedor_id, 
            :usuario_id
        ) 
        RETURNING *
        """),
        {
            "nombre": producto.nombre,
            "descripcion": producto.descripcion or None,  # Convierte "" a NULL
            "precio": producto.precio,
            "stock": producto.stock,
            "categoria_id": producto.categoria_id,
            "proveedor_id": producto.proveedor_id,
            "usuario_id": producto.usuario_id
        }
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