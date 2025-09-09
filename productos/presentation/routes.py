from typing import Any, Dict, Optional, Set, Union
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Row
from ...database.session import get_db
from ...productos.presentation import schemas
from ...database.UnitofWork import UnitOfWork
from ..application.service import ProductService
from ..infrastructure.repositories import ProductRepository
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/productos", tags=["productos"])

def fila_a_diccionario(
    fila: Union[Row, object], 
    exclude: Optional[Set[str]] = None
) -> Dict[str, Any]:
    try:
        if hasattr(fila, "__table__"):
            return {c.name: getattr(fila, c.name) for c in fila.__table__.columns if exclude is None or c.name not in exclude}
        elif isinstance(fila, Row):
            return dict(fila._mapping)
        elif isinstance(fila, dict):
            return {k: v for k, v in fila.items() if exclude is None or k not in exclude}
        raise ValueError("Tipo de objeto no soportado para conversión")
    except Exception as e:
        logger.error(f"Error convirtiendo fila a diccionario: {str(e)}")
        raise ValueError(f"No se pudo convertir el objeto: {str(e)}")

async def get_product_service(db: AsyncSession = Depends(get_db)):
    repository = ProductRepository(db)
    return ProductService(repository)

@router.get("/", response_model=list[schemas.Producto])
async def listar_productos(service: ProductService = Depends(get_product_service)):
    productos = await service.get_all_products()
    return productos

@router.post("/CrearProductos", response_model=schemas.Producto, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto: schemas.ProductoCreate,
    service: ProductService = Depends(get_product_service),
    db: AsyncSession = Depends(get_db)
):
    uow = UnitOfWork(db)
    try:
        async with uow.transaction():
            new_product = await service.create_product(producto)
            return fila_a_diccionario(new_product)
    except Exception as e:
        logger.error(f"Error al crear producto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear producto: {e}"
        )

@router.get("/{producto_id}", response_model=schemas.Producto)
async def obtener_producto(
    producto_id: int = Path(..., gt=0),
    service: ProductService = Depends(get_product_service)
):
    product = await service.get_product(producto_id)
    return fila_a_diccionario(product)

@router.get(
    "/producto/{nombre_producto}",
    response_model=schemas.Producto,
    summary="Obtener producto por nombre",
    description="Recupera un producto específico por su nombre exacto"
)
async def obtener_producto_por_nombre(
    nombre_producto: str = Path(..., description="Nombre exacto del producto a buscar"),
    service: ProductService = Depends(get_product_service)
):
    producto = await service.get_product_nom(nombre_producto)
    return fila_a_diccionario(producto)

@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_producto(
    producto_id: int = Path(..., gt=0),
    service: ProductService = Depends(get_product_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        await service.get_product_by_id(producto_id)
        deleted = await service.delete_product(producto_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo eliminar el producto"
            )
        return None
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error eliminando producto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar producto"
        )

# Endpoint para actualizar un producto
# @router.put("/actualizar/{product_id}", response_model=schemas.Producto)
@router.patch("/actualizar/{product_id}", response_model=schemas.Producto)
async def update_product(
    product_id: int, 
    product_data: schemas.ProductoUpdate, 
    service: ProductService = Depends(get_product_service)
):
    """
    Actualiza un producto existente.
    
    - **product_id**: ID del producto a actualizar
    - **product_data**: Campos a actualizar (parcial o completo)
    """
    try:
        return await service.update_product(product_id, product_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el producto: {str(e)}"
        )