from os import stat
from fastapi import APIRouter, Depends, HTTPException, Path, logger, status
from sqlalchemy.ext.asyncio import AsyncSession

# import 
from ...application.proveedores_service import ProveedoresService
from ...application.proveedores_service import PorveedoresRepository
from ....database.session import get_db
from typing import List
from pydantic import BaseModel

proveedores_router = APIRouter(prefix="/proveedores", tags=["proveedores"])

# schemas
class ProveedoresBase(BaseModel):
    nombre: str


class ProveedoresCreate(ProveedoresBase):
    pass

class ProveedoresOut(ProveedoresBase):
    id: int # cambia a proveedores_id si es el nombre en tu models
    
    class Config:
        from_attributes = True 

#endpoint mostrar_Proveedores
proveedores_router.get("/", response_model=list[ProveedoresOut])
async def listar_todas_Proveedores(
        session: AsyncSession = Depends(get_db),
        skip: int = 0,
        limit: int = 100
):
    repo = PorveedoresRepository(session)
    service = ProveedoresService(repo)
    return await service.obtener_proveedores(skip=skip, limit=limit)