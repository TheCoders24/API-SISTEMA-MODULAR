# presentation/routes/categoria_router.py
from os import stat
from fastapi import APIRouter, Depends, HTTPException, Path, logger, status
from sqlalchemy.ext.asyncio import AsyncSession

#from productos.application import service
from ....productos.application import service
from ...application.categoria_service import CategoriaService
from ...application.categoria_service import CategoriaRepository
from ....database.session import get_db
from typing import List
from pydantic import BaseModel

categoria_router = APIRouter(prefix="/categorias", tags=["categorias"])

# Schemas
class CategoriaBase(BaseModel):
    nombre: str

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaOut(CategoriaBase):
    id: int  # Cambia a categoria_id si es el nombre en tu modelo
    
    class Config:
        from_attributes = True  # Pydantic v2 (antes orm_mode)

# Endpoints de Obtener o listar_todas_categorias
@categoria_router.get("/", response_model=List[CategoriaOut])
async def listar_todas_categorias(
    session: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    repo = CategoriaRepository(session)
    service = CategoriaService(repo)
    return await service.obtener_todas_categorias()


# endpoint de obtener_categoria por el categoria_id
@categoria_router.get("/{categoria_id}", response_model=CategoriaOut)
async def obtener_categoria(
    categoria_id: int,
    session: AsyncSession = Depends(get_db)
):
    repo = CategoriaRepository(session)
    service = CategoriaService(repo)
    categoria = await service.obtener_categoria_por_id(categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return categoria

# endpoint de crear las categorias
@categoria_router.post("/", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
async def crear_categoria(
    categoria: CategoriaCreate,
    session: AsyncSession = Depends(get_db)
):
    repo = CategoriaRepository(session)
    service = CategoriaService(repo)
    return await service.crear_categoria(categoria)