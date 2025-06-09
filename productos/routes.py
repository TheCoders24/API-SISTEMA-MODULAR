from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Row
import sqlalchemy as sa
from ..database.session import get_db
from . import schemas
from ..database.UnitofWork import UnitOfWork
from . import schemas
from .service import ProductService
from .repositories import ProductRepository

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

