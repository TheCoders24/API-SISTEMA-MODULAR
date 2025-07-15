from fastapi import APIRouter, Depends, HTTPException, Path, Query, logger, status
from sqlalchemy.ext.asyncio import AsyncSession
# import 
from ...application.proveedores_service import ProveedoresService
from ...application.proveedores_service import PorveedoresRepository
from ....database.session import get_db
from typing import List
from pydantic import BaseModel

#rutas en la url
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
@proveedores_router.get(
    "/",
    response_model=List[ProveedoresOut],
    status_code=status.HTTP_200_OK,
    summary="Obtener todos los proveedores",
    description="Retorna una lista paginada de todos los proveedores registrados"
)
async def listar_proveedores(
    skip: int = Query(0, ge=0, description="Items a saltar"),
    limit: int = Query(100, le=500, description="Límite de items por página"),
    session: AsyncSession = Depends(get_db)
):
    try:
        repo = PorveedoresRepository(session)
        service = ProveedoresService(repo)
        proveedores = await service.obtener_proveedores(skip=skip, limit=limit)
        
        if not proveedores:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron proveedores"
            )
            
        return proveedores
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener proveedores: {str(e)}"
        )