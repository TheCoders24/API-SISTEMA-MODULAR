from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from pydantic import BaseModel, Field

# Importar servicios - CORREGIDO: 'infrastructure' no 'infraestructure'
try:
   
    from ...infraestructure.services.metricas_service import MetricasService
    from ...infraestructure.services.alertas_service import AlertasService

except ImportError:
    # Si la estructura es diferente, ajusta según tu proyecto
    from infraestructure.services.metricas_service import MetricasService
    from infraestructure.services.alertas_service import AlertasService
   

# Importar entidades/enums del dominio - CORREGIDO: 'alertas' no 'Alertas'
try:
    from ...domain.entities.metricas import Periodo, Tendencia
    from ...domain.entities.Alertas import TipoAlerta, SeveridadAlerta  # 'alertas' en minúscula
except ImportError:
    from domain.entities.metricas import Periodo, Tendencia
    from domain.entities.Alertas import TipoAlerta, SeveridadAlerta

# Crear router
router = APIRouter()
logger = logging.getLogger(__name__)

# =========== DEPENDENCIAS ===========
def get_metricas_service() -> MetricasService:
    return MetricasService()

def get_alertas_service() -> AlertasService:
    return AlertasService()

# =========== SCHEMAS PYDANTIC ===========
class MetricaResumenResponse(BaseModel):
    id: str
    nombre: str
    valor: str
    cambio: str
    tendencia: str
    icono: str
    color: str
    categoria: str

class MetricaDetalleResponse(BaseModel):
    id: str
    nombre: str
    valor_actual: float
    cambio_porcentual: float
    unidad: str
    meta: float
    progreso_meta: float

class KPIResponse(BaseModel):
    id: str
    nombre: str
    valor: float
    unidad: str
    objetivo: float
    progreso: float
    estado: str

class InsightResponse(BaseModel):
    tipo: str
    titulo: str
    descripcion: str
    impacto: str

class DashboardResponse(BaseModel):
    id: str
    nombre: str
    metricas_resumen: List[MetricaResumenResponse]
    metricas_detalle: List[MetricaDetalleResponse]
    graficos: List[Dict[str, Any]]
    kpis: List[KPIResponse]
    fecha_actualizacion: str
    analisis_insights: List[InsightResponse]

class RealtimeMetricsResponse(BaseModel):
    usuarios_conectados: int
    pedidos_pendientes: int
    tickets_soporte: int
    tiempo_respuesta: float
    timestamp: str

class AlertaResponse(BaseModel):
    id: str
    tipo: str
    titulo: str
    descripcion: str
    metrica_id: str
    severidad: str
    fecha_deteccion: str
    accion_recomendada: Optional[str] = None
    resuelta: bool

class AlertaCreateRequest(BaseModel):
    tipo: TipoAlerta  # CORREGIDO: Usar el enum TipoAlerta
    titulo: str = Field(..., min_length=5, max_length=200)
    descripcion: str = Field(..., min_length=10, max_length=1000)
    metrica_id: str = Field(...)
    severidad: SeveridadAlerta  # CORREGIDO: Usar el enum SeveridadAlerta
    accion_recomendada: Optional[str] = Field(None, max_length=500)

class EstadisticasAlertasResponse(BaseModel):
    total: int
    activas: int
    resueltas: int
    por_severidad: Dict[str, int]
    por_tipo: Dict[str, int]
    ultima_actualizacion: str

# =========== ENDPOINTS DE MÉTRICAS ===========
@router.get("/dashboard", response_model=DashboardResponse)
async def obtener_dashboard(
    periodo: Periodo = Query(Periodo.MENSUAL, description="Período de tiempo"),
    usuario_id: Optional[str] = Query(None, description="ID del usuario"),
    metricas_service: MetricasService = Depends(get_metricas_service)
):
    """
    Obtener dashboard completo de métricas
    """
    try:
        dashboard = await metricas_service.obtener_dashboard(periodo.value, usuario_id)
        return dashboard
    except Exception as e:
        logger.error(f"Error al obtener dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar dashboard: {str(e)}"
        )

@router.get("/realtime", response_model=RealtimeMetricsResponse)
async def obtener_metricas_realtime(
    metricas_service: MetricasService = Depends(get_metricas_service)
):
    """
    Obtener métricas en tiempo real
    """
    try:
        realtime = await metricas_service.obtener_metricas_realtime()
        return realtime
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

@router.get("/resumen")
async def obtener_resumen_metricas(
    periodo: Periodo = Query(Periodo.MENSUAL, description="Período de tiempo"),
    metricas_service: MetricasService = Depends(get_metricas_service)
):
    """
    Obtener resumen de métricas principales
    """
    try:
        dashboard = await metricas_service.obtener_dashboard(periodo.value)
        return {
            "success": True,
            "data": {
                "metricas_resumen": dashboard["metricas_resumen"],
                "kpis": dashboard["kpis"],
                "timestamp": dashboard["fecha_actualizacion"]
            }
        }
    except Exception as e:
        logger.error(f"Error al obtener resumen: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar resumen: {str(e)}"
        )

# =========== ENDPOINTS DE ALERTAS ===========
@router.get("/alertas", response_model=List[AlertaResponse])
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
        return alertas
    except Exception as e:
        logger.error(f"Error al obtener alertas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar alertas: {str(e)}"
        )

@router.post("/alertas", response_model=AlertaResponse, status_code=status.HTTP_201_CREATED)
async def crear_alerta(
    alerta_data: AlertaCreateRequest,
    alertas_service: AlertasService = Depends(get_alertas_service)
):
    """
    Crear una nueva alerta
    """
    try:
        # CORREGIDO: Usar model_dump() en lugar de dict() para Pydantic v2
        alerta = await alertas_service.crear_alerta(alerta_data.model_dump())
        return alerta
    except Exception as e:
        logger.error(f"Error al crear alerta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear alerta: {str(e)}"
        )

@router.get("/alertas/estadisticas", response_model=EstadisticasAlertasResponse)
async def obtener_estadisticas_alertas(
    alertas_service: AlertasService = Depends(get_alertas_service)
):
    """
    Obtener estadísticas de alertas
    """
    try:
        estadisticas = await alertas_service.obtener_estadisticas()
        return estadisticas
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar estadísticas: {str(e)}"
        )

@router.put("/alertas/{alerta_id}/resolver")
async def resolver_alerta(
    alerta_id: str,
    alertas_service: AlertasService = Depends(get_alertas_service)
):
    """
    Marcar una alerta como resuelta
    """
    try:
        # Implementación básica - puedes mejorarla
        from datetime import datetime
        
        # Obtener todas las alertas
        alertas = await alertas_service.obtener_alertas_activas()
        
        # Buscar la alerta
        alerta_encontrada = None
        for alerta in alertas:
            if alerta.get("id") == alerta_id:
                alerta_encontrada = alerta
                break
        
        if not alerta_encontrada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alerta {alerta_id} no encontrada"
            )
        
        # Marcar como resuelta (esto es una simulación)
        alerta_encontrada["resuelta"] = True
        
        return {
            "success": True,
            "message": f"Alerta {alerta_id} marcada como resuelta",
            "data": {
                "id": alerta_id,
                "resuelta": True,
                "fecha_resolucion": datetime.now().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al resolver alerta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al resolver alerta: {str(e)}"
        )

@router.get("/alertas/{alerta_id}")
async def obtener_alerta_detalle(
    alerta_id: str,
    alertas_service: AlertasService = Depends(get_alertas_service)
):
    """
    Obtener detalle de una alerta específica
    """
    try:
        alertas = await alertas_service.obtener_alertas_activas()
        alerta = next((a for a in alertas if a.get("id") == alerta_id), None)
        
        if not alerta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alerta {alerta_id} no encontrada"
            )
        
        return {
            "success": True,
            "data": alerta
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener alerta: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cargar alerta: {str(e)}"
        )

# =========== ENDPOINTS DE CONFIGURACIÓN ===========
@router.post("/kpis")
async def crear_kpi_config(
    nombre: str = Body(...),
    metrica_id: str = Body(...),
    objetivo: float = Body(...),
    unidad: str = Body(...),
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

# Endpoint adicional para probar la conexión
@router.get("/test")
async def test_endpoint():
    """
    Endpoint de prueba para verificar que las rutas funcionan
    """
    return {
        "status": "ok",
        "message": "Rutas de métricas y alertas funcionando",
        "timestamp": datetime.now().isoformat()
    }