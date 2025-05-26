from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Row
import sqlalchemy as sa
from ..database.session import get_db
from . import schemas


router = APIRouter(prefix="/productos", tags=["productos"])


def row_to_dict(row: Row) -> dict:
    return dict(row._mapping)


# Crear producto
@router.post("/", response_model=schemas.Producto, status_code=status.HTTP_201_CREATED)
async def crear_producto(producto: schemas.ProductoCreate, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(
            sa.text("SELECT id FROM productos WHERE nombre = :nombre"),
            {"nombre": producto.nombre}
        )
        if existing.fetchone():
            raise HTTPException(status_code=400, detail="Ya existe un producto con ese nombre")

        result = await db.execute(
            sa.text("""
                INSERT INTO productos (nombre, descripcion, precio, stock, categoria_id, proveedor_id, usuario_id)
                VALUES (:nombre, :descripcion, :precio, :stock, :categoria_id, :proveedor_id, :usuario_id)
                RETURNING *
            """),
            {
                "nombre": producto.nombre,
                "descripcion": producto.descripcion or None,
                "precio": producto.precio,
                "stock": producto.stock,
                "categoria_id": producto.categoria_id,
                "proveedor_id": producto.proveedor_id,
                "usuario_id": producto.usuario_id
            }
        )
        await db.commit()
        row = result.fetchone()
        return row_to_dict(row)

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear producto")


# Obtener un producto por ID
@router.get("/{producto_id}", response_model=schemas.Producto)
async def obtener_producto(producto_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            sa.text("SELECT * FROM productos WHERE id = :id"),
            {"id": producto_id}
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return row_to_dict(row)

    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al consultar producto")


# Listar todos los productos
@router.get("/", response_model=list[schemas.Producto])
async def listar_productos(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(sa.text("SELECT * FROM productos"))
        return [row_to_dict(row) for row in result.fetchall()]
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al listar productos")


# Actualizar un producto completo
@router.put("/{producto_id}", response_model=schemas.Producto)
async def actualizar_producto(producto_id: int, datos: schemas.ProductoUpdate, db: AsyncSession = Depends(get_db)):
    try:
        # Verificar existencia
        result = await db.execute(sa.text("SELECT id FROM productos WHERE id = :id"), {"id": producto_id})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        result = await db.execute(
            sa.text("""
                UPDATE productos
                SET nombre = :nombre,
                    descripcion = :descripcion,
                    precio = :precio,
                    stock = :stock,
                    categoria_id = :categoria_id,
                    proveedor_id = :proveedor_id,
                    usuario_id = :usuario_id
                WHERE id = :id
                RETURNING *
            """),
            {
                "id": producto_id,
                "nombre": datos.nombre,
                "descripcion": datos.descripcion or None,
                "precio": datos.precio,
                "stock": datos.stock,
                "categoria_id": datos.categoria_id,
                "proveedor_id": datos.proveedor_id,
                "usuario_id": datos.usuario_id
            }
        )
        await db.commit()
        row = result.fetchone()
        return row_to_dict(row)

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar producto")


# Actualizar solo el stock
@router.patch("/{producto_id}/stock", response_model=schemas.Producto)
async def actualizar_stock(producto_id: int, stock: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(sa.text("SELECT id FROM productos WHERE id = :id"), {"id": producto_id})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        await db.execute(
            sa.text("UPDATE productos SET stock = :stock WHERE id = :id"),
            {"stock": stock, "id": producto_id}
        )
        await db.commit()

        result = await db.execute(sa.text("SELECT * FROM productos WHERE id = :id"), {"id": producto_id})
        row = result.fetchone()
        return row_to_dict(row)

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar stock")


# Eliminar producto
@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_producto(producto_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(sa.text("SELECT id FROM productos WHERE id = :id"), {"id": producto_id})
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        await db.execute(sa.text("DELETE FROM productos WHERE id = :id"), {"id": producto_id})
        await db.commit()

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error al eliminar producto")
