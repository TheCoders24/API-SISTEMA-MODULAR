# presentation/routes/categoria_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ...application.categoria_service import CategoriaService
from ...application.categoria_service import CategoriaRepository
from ....database.session import get_db
from typing import List
from pydantic import BaseModel

categoria_router = APIRouter(prefix="/categorias", tags=["categorias"])

class CategoriaOut(BaseModel):
    id: int
    nombre: str

    class Config:
        orm_mode = True
        
@categoria_router.get("/", response_model=list[CategoriaOut])
async def listar_categorias(session: AsyncSession = Depends(get_db)):
    repo = CategoriaRepository(session)
    service = CategoriaService(repo)
    return await service.obtener_categoria()