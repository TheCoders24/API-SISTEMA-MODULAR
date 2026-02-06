from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import List, Optional
import logging
from ...infraestructure.services.alertas_service import AlertasService
from ...domain.entities.Alertas import TipoAlerta, SeveridadAlerta

router = APIRouter(prefix="/api/alertas", tags=["alertas"])
logger = logging.getLogger(__name__)

def get_alertas_service() -> AlertasService:
    return AlertasService()

@router.get("/")
async def obtener_alertas_activas(
    severidad: Optional[SeveridadAlerta] = Query(None, description="Filtrar por severidad"),
    tipo: Optional[TipoAlerta] = Query(None, description="Filtrar por tipo"),
    alertas_service: AlertasService = Depends(get_alertas_service)
):
    """
    Obtener alertas activas
    """
    try:
        alertas = await alertas_service.obtener_alertas_activas(
            severidad.value if severidad else None,
            tipo.value if tipo else None
        )
        return {
            "success": True,
            "data": alertas,
            "total": len(alertas)
        }
    except Exception as e:
        logger.error(f"Error al obtener alertas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar alertas: {str(e)}"
        )

@router.post("/")
async def crear_alerta(
    tipo: TipoAlerta = Body(...),
    titulo: str = Body(...),
    descripcion: str = Body(...),
    metrica_id: str = Body(...),
    severidad: SeveridadAlerta = Body(...),
    accion_recomendada: Optional[str] = Body(None),
    alertas_service: AlertasService = Depends(get_alertas_service)
):
    """
    Crear una nueva alerta
    """
    try:
        alerta = await alertas_service.crear_alerta({
            "tipo": tipo.value,
            "titulo": titulo,
            "descripcion": descripcion,
            "metrica_id": metrica_id,
            "severidad": severidad.value,
            "accion_recomendada": accion_recomendada
        })
        return {
            "success": True,
            "message": "Alerta creada exitosamente",
            "data": alerta
        }
    except Exception as e:
        logger.error(f"Error al crear alerta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear alerta: {str(e)}"
        )

@router.get("/estadisticas")
async def obtener_estadisticas(
    alertas_service: AlertasService = Depends(get_alertas_service)
):
    """
    Obtener estadísticas de alertas
    """
    try:
        estadisticas = await alertas_service.obtener_estadisticas()
        return {
            "success": True,
            "data": estadisticas
        }
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar estadísticas: {str(e)}"
        )

@router.put("/{alerta_id}/resolver")
async def resolver_alerta(
    alerta_id: str,
    alertas_service: AlertasService = Depends(get_alertas_service)
):
    """
    Resolver una alerta
    """
    try:
        alerta = await alertas_service.resolver_alerta(alerta_id)
        return {
            "success": True,
            "message": "Alerta resuelta exitosamente",
            "data": alerta
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al resolver alerta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al resolver alerta: {str(e)}"
        )