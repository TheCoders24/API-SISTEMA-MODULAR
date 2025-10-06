from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...application.proveedores_service import ProveedoresService
from ...infrastructure.proveedores_repository import ProveedoresRepository
from ...domain.schemas import ProveedorCreate,ProveedorUpdate,ProveedorOut
from ....database.session import get_db
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# Configuración del router
proveedores_router = APIRouter(prefix="/proveedores", tags=["proveedores"])

# Schemas basados en tu tabla
class ProveedoresBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del proveedor")
    contacto: Optional[str] = Field(None, max_length=100, description="Persona de contacto")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    email: Optional[EmailStr] = Field(None, description="Email de contacto")

class ProveedoresCreate(ProveedoresBase):
    pass

class ProveedoresUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    contacto: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None)

class ProveedoresOut(ProveedoresBase):
    id: int
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Dependencia para el servicio
async def get_proveedores_service(session: AsyncSession = Depends(get_db)) -> ProveedoresService:
    repo = ProveedoresRepository(session)
    return ProveedoresService(repo)

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
        repo = ProveedoresRepository(session)
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

#endpoint obtener_proveedor_por_id
@proveedores_router.get(
    "/{proveedor_id}",
    response_model=ProveedoresOut,
    status_code=status.HTTP_200_OK,
    summary="Obtener un proveedor por ID",
    description="Retorna los detalles de un proveedor específico"
)
async def obtener_proveedor(
    proveedor_id: int = Path(..., gt=0, description="ID del proveedor"),
    service: ProveedoresService = Depends(get_proveedores_service)
):
    try:
        proveedor = await service.obtener_proveedor_por_id(proveedor_id)
        
        if not proveedor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proveedor con ID {proveedor_id} no encontrado"
            )
            
        return proveedor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener el proveedor: {str(e)}"
        )

#endpoint crear_proveedor
@proveedores_router.post(
    "/",
    response_model=ProveedoresOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo proveedor",
    description="Crea un nuevo proveedor en el sistema"
)
async def crear_proveedor(
    proveedor_data: ProveedoresCreate,
    service: ProveedoresService = Depends(get_proveedores_service)
):
    try:
        # Verificar si ya existe un proveedor con el mismo nombre
        existe = await service.verificar_proveedor_existente(proveedor_data.nombre)
        if existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un proveedor con ese nombre"
            )
        
        nuevo_proveedor = await service.crear_proveedor(proveedor_data)
        return nuevo_proveedor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el proveedor: {str(e)}"
        )

#endpoint actualizar_proveedor
@proveedores_router.put(
    "/{proveedor_id}",
    response_model=ProveedoresOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar un proveedor",
    description="Actualiza la información de un proveedor existente"
)
async def actualizar_proveedor(
    proveedor_data: ProveedoresUpdate,
    proveedor_id: int = Path(..., gt=0, description="ID del proveedor"),
    service: ProveedoresService = Depends(get_proveedores_service)
):
    try:
        proveedor_actualizado = await service.actualizar_proveedor(proveedor_id, proveedor_data)
        return proveedor_actualizado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el proveedor: {str(e)}"
        )

#endpoint eliminar_proveedor
@proveedores_router.delete(
    "/{proveedor_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar un proveedor",
    description="Elimina un proveedor del sistema"
)
async def eliminar_proveedor(
    proveedor_id: int = Path(..., gt=0, description="ID del proveedor"),
    service: ProveedoresService = Depends(get_proveedores_service)
):
    try:
        await service.eliminar_proveedor(proveedor_id)
        
        return {
            "message": f"Proveedor con ID {proveedor_id} eliminado correctamente",
            "proveedor_id": proveedor_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el proveedor: {str(e)}"
        )

#endpoint buscar_proveedores_por_nombre
@proveedores_router.get(
    "/buscar/{nombre}",
    response_model=List[ProveedoresOut],
    status_code=status.HTTP_200_OK,
    summary="Buscar proveedores por nombre",
    description="Busca proveedores cuyo nombre coincida con el término de búsqueda"
)
async def buscar_proveedores(
    nombre: str = Path(..., description="Término de búsqueda"),
    service: ProveedoresService = Depends(get_proveedores_service)
):
    try:
        proveedores = await service.buscar_proveedores_por_nombre(nombre)
        
        if not proveedores:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron proveedores con el nombre: {nombre}"
            )
            
        return proveedores
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar proveedores: {str(e)}"
        )