from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
import logging
from ...infraestructure.services.metricas_service import MetricasService
from ...domain.entities.metricas import Periodo

router = APIRouter(prefix="/api/metricas", tags=["metricas"])
logger = logging.getLogger(__name__)

def get_metricas_service() -> MetricasService:
    return MetricasService()

@router.get("/dashboard")
async def obtener_dashboard(
    periodo: Periodo = Query(Periodo.MENSUAL, description="Período de tiempo"),
    usuario_id: Optional[str] = Query(None, description="ID del usuario"),
    metricas_service: MetricasService = Depends(get_metricas_service)
):
    """
    Obtener dashboard de métricas
    """
    try:
        dashboard = await metricas_service.obtener_dashboard(periodo.value, usuario_id)
        return {
            "success": True,
            "data": dashboard,
            "periodo": periodo.value
        }
    except Exception as e:
        logger.error(f"Error al obtener dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar dashboard: {str(e)}"
        )

@router.get("/realtime")
async def obtener_metricas_realtime(
    metricas_service: MetricasService = Depends(get_metricas_service)
):
    """
    Obtener métricas en tiempo real
    """
    try:
        realtime = await metricas_service.obtener_metricas_realtime()
        return {
            "success": True,
            "data": realtime,
            "timestamp": realtime["timestamp"]
        }
    except Exception as e:
        logger.error(f"Error al obtener métricas en tiempo real: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar métricas en tiempo real: {str(e)}"
        )

@router.get("/historico")
async def obtener_metricas_historicas(
    metrica_id: str = Query(..., description="ID de la métrica"),
    dias: int = Query(7, ge=1, le=365, description="Número de días"),
    metricas_service: MetricasService = Depends(get_metricas_service)
):
    """
    Obtener datos históricos de una métrica
    """
    try:
        historico = await metricas_service.obtener_metricas_historicas(metrica_id, dias)
        return {
            "success": True,
            "data": {
                "metrica_id": metrica_id,
                "datos": historico,
                "dias": dias
            }
        }
    except Exception as e:
        logger.error(f"Error al obtener datos históricos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar datos históricos: {str(e)}"
        )

@router.post("/kpis")
async def crear_kpi_config(
    nombre: str,
    metrica_id: str,
    objetivo: float,
    unidad: str,
    metricas_service: MetricasService = Depends(get_metricas_service)
):
    """
    Crear configuración de KPI
    """
    try:
        kpi_config = await metricas_service.crear_kpi_config(nombre, metrica_id, objetivo, unidad)
        return {
            "success": True,
            "message": "KPI creado exitosamente",
            "data": kpi_config
        }
    except Exception as e:
        logger.error(f"Error al crear KPI: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear KPI: {str(e)}"
        )