from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# from ..application.categoria_service import CategoriaService
# from ..infraestructura.categoria_repository import CategoriaRepository
from ...infraestructura.categoria_repository import CategoriaRepository
from ...application.categoria_service import CategoriaService
from ....database.session import get_db
from ...domain.models import Categoria, CategoriaBase, CategoriaCreate, CategoriaOut
from pydantic import BaseModel

categoria_router = APIRouter(
    prefix="/categorias",
    tags=["categorias"],
    responses={404: {"description": "No encontrado"}}
)

# Dependency
def get_categoria_service(session: AsyncSession = Depends(get_db)) -> CategoriaService:
    repo = CategoriaRepository(session)
    return CategoriaService(repo)

# Endpoints
@categoria_router.get("/", response_model=List[CategoriaOut], summary="Obtener todas las categorías")
async def listar_todas_categorias(
    service: CategoriaService = Depends(get_categoria_service),
    skip: int = 0,
    limit: int = 100
):
    """
    Obtiene una lista de todas las categorías existentes.
    
    Parámetros:
    - skip: Número de categorías a saltar (para paginación)
    - limit: Número máximo de categorías a devolver (para paginación)
    """
    return await service.obtener_todas_categorias()

@categoria_router.get(
    "/{categoria_id}", 
    response_model=CategoriaOut,
    summary="Obtener categoría por ID",
    responses={
        404: {"description": "Categoría no encontrada"}
    }
)
async def obtener_categoria(
    categoria_id: int,
    service: CategoriaService = Depends(get_categoria_service)
):
    """
    Obtiene una categoría específica por su ID.
    
    Parámetros:
    - categoria_id: ID de la categoría a buscar
    """
    categoria = await service.obtener_categoria_por_id(categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return categoria

@categoria_router.post(
    "/CrearCategoria",
    response_model=CategoriaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva categoría",
    responses={
        400: {"description": "Nombre de categoría ya existe"},
        500: {"description": "Error interno del servidor"}
    }
)
async def crear_categoria(
    categoria_data: CategoriaCreate,
    service: CategoriaService = Depends(get_categoria_service)
):
    """
    Crea una nueva categoría.
    
    Parámetros:
    - nombre: Nombre de la nueva categoría (debe ser único)
    """
    try:
        return await service.crear_categoria(categoria_data.nombre)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )