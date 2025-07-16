from typing import Any, Dict, Optional, Set, Union
from unittest.mock import Base
from fastapi import APIRouter, Depends, HTTPException, Path, logger, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Row
import sqlalchemy as sa
from ...database.session import get_db
from ...productos.presentation import schemas
from ...database.UnitofWork import UnitOfWork
from ..application.service import ProductService
from ..infrastructure.repositories import ProductRepository
import logging
from fastapi.logger import logger as fastapi_logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/productos", tags=["productos"])


def row_to_dict(row: Row) -> dict:
    return dict(row._mapping)


# Dependencia para el servicio
async def get_product_service(db: AsyncSession = Depends(get_db)):
    repository = ProductRepository(db)
    return ProductService(repository)

# productos/routes.py
@router.get("/", response_model=list[schemas.Producto])
async def listar_productos(
    service: ProductService = Depends(get_product_service)
):
    """Obtiene el listado completo de productos"""
    return await service.get_all_products()

# Crear producto
"""
@router.post("/CrearProductos", response_model=schemas.Producto, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto: schemas.ProductoCreate,
    service: ProductService = Depends(get_product_service),
    db: AsyncSession = Depends(get_db)
):
    uow = UnitOfWork(db)
    async with uow.transaction():
        try:
            new_product = await service.create_product(producto)
            return row_to_dict(new_product)
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear producto: {str(e)}"
            )
"""
#"""
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
            return row_to_dict(new_product)
    except Exception as e:
        print("Error al crear producto:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear producto: {str(e)}"
        )
#"""
"""
@router.post(
    "/CrearProductos",
    response_model=schemas.Producto,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo producto",
    responses={
        404: {"description": "Categoría o proveedor no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)
async def crear_producto(
    producto: schemas.ProductoCreate,
    service: ProductService = Depends(get_product_service),
    db: AsyncSession = Depends(get_db)
):
    uow = UnitOfWork(db)
    try:
        # Verificar existencia de categoría y proveedor
        async with uow.transaction():
            # Verificar categoría
            categoria = await uow.repository.get_by_id(categoria, producto.categoria_id)
            if not categoria:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoría con ID {producto.categoria_id} no existe"
                )
            
            # Verificar proveedor
            proveedor = await uow.repository.get_by_id(proveedor, producto.proveedor_id)
            if not proveedor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Proveedor con ID {producto.proveedor_id} no existe"
                )
            
            # Crear producto si las relaciones existen
            new_product = await service.create_product(producto)
            return row_to_dict(new_product)
            
    except HTTPException:
        raise  # Re-lanza las excepciones HTTP que ya hemos capturado
    except Exception as e:
        await uow.rollback()
        logger.error(f"Error al crear producto: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear producto: {str(e)}"
        )
"""

# Obtener producto
@router.get("/{producto_id}", response_model=schemas.Producto)
async def obtener_producto(
    producto_id: int,
    service: ProductService = Depends(get_product_service)
):
    try:
        product = await service.get_product(producto_id)
        return row_to_dict(product)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar producto: {str(e)}"
        )


@router.get(
    "/producto/{nombre_producto}",
    response_model=schemas.Producto,
    responses={
        200: {"description": "Producto encontrado exitosamente"},
        404: {"description": "Producto no encontrado"},
        500: {"description": "Error interno del servidor"}
    },
    summary="Obtener producto por nombre",
    description="Recupera un producto específico por su nombre exacto"
)
async def obtener_producto_por_nombre(
    nombre_producto: str = Path(..., description="Nombre exacto del producto a buscar"),
    servicio: ProductService = Depends(get_product_service)
) -> schemas.Producto:
    """
    Obtiene un producto por su nombre exacto.
    
    Parámetros:
        nombre_producto: Nombre exacto del producto a recuperar
        servicio: Servicio de Productos inyectado
        
    Retorna:
        esquemas.Producto: El producto solicitado
        
    Excepciones:
        HTTPException: 404 si el producto no existe, 500 para errores del servidor
    """
    try:
        producto = await servicio.get_product_nombre(nombre_producto)
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el producto con nombre '{nombre_producto}'"
            )
        return fila_a_diccionario(producto)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error al obtener producto '{nombre_producto}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al recuperar el producto"
        )

def fila_a_diccionario(
    fila: Union[Row, Base], 
    exclude: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Convierte una fila de base de datos (SQLAlchemy) a diccionario.
    
    Args:
        fila: Objeto SQLAlchemy o Row a convertir
        exclude: Campos a excluir (opcional)
        
    Returns:
        Diccionario con los datos de la fila
        
    Raises:
        ValueError: Si el objeto no es convertible
    """
    try:
        if hasattr(fila, "__table__"):  # Es un modelo SQLAlchemy
            return {c.name: getattr(fila, c.name) 
                   for c in fila.__table__.columns
                   if exclude is None or c.name not in exclude}
        
        elif isinstance(fila, Row):  # Es un Row de SQLAlchemy
            return dict(fila._mapping)
            
        elif isinstance(fila, dict):  # Ya es un diccionario
            return {k: v for k, v in fila.items() 
                   if exclude is None or k not in exclude}
            
        raise ValueError("Tipo de objeto no soportado para conversión")
        
    except Exception as e:
        logger.error(f"Error convirtiendo fila a diccionario: {str(e)}")
        raise ValueError(f"No se pudo convertir el objeto: {str(e)}")
    

    
# Endpoint del methodo eliminar productos
@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_producto(
    producto_id: int = Path(..., gt=0),
    service: ProductService = Depends(get_product_service),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Primero verificar existencia
        product = await service.get_product_by_id(producto_id)
        
        # Luego eliminar
        deleted = await service.delete_product(producto_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo eliminar el producto"
            )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error eliminando producto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar producto"
        )