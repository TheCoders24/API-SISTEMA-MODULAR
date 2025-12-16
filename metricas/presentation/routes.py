# metricas/routes.py
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta

from ..models.models import (
    Periodo, TipoGrafico, DashboardCompleto, MetricaDetalle,
    GraficoMetrica, AnalisisComparativo, AlertaMetrica,
    SerieTemporalCompleta, FiltroMetricas, ConfiguracionDashboard
)
from ..domain.service import MetricasService

router = APIRouter(prefix="/metricas", tags=["metricas"])
service = MetricasService()

# ========== DASHBOARD ==========
@router.get("/dashboard", response_model=DashboardCompleto)
async def obtener_dashboard(
    periodo: Periodo = Periodo.MENSUAL,
    categorias: Optional[str] = Query(None, description="Categorías separadas por coma"),
    metricas: Optional[str] = Query(None, description="IDs de métricas separadas por coma")
):
    """Obtener dashboard completo de métricas"""
    try:
        # Crear filtros si se especifican
        filtros = None
        if categorias or metricas:
            categorias_list = categorias.split(",") if categorias else None
            metricas_list = metricas.split(",") if metricas else None
            
            # En una implementación real, convertirías metricas_list a TipoMetrica
            filtros = FiltroMetricas(
                categorias=categorias_list,
                metricas=[]  # Esto sería la conversión real
            )
        
        return await service.obtener_dashboard(periodo, filtros)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo dashboard: {str(e)}"
        )

# ========== MÉTRICAS INDIVIDUALES ==========
@router.get("/{metrica_id}", response_model=MetricaDetalle)
async def obtener_metrica(metrica_id: str):
    """Obtener detalle de una métrica específica"""
    try:
        metrica = await service.obtener_metrica_detalle(metrica_id)
        if not metrica:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Métrica '{metrica_id}' no encontrada"
            )
        return metrica
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo métrica: {str(e)}"
        )

# ========== GRÁFICOS ==========
@router.get("/graficos/{grafico_id}", response_model=GraficoMetrica)
async def obtener_grafico(
    grafico_id: str,
    personalizar: Optional[bool] = Query(False, description="Personalizar gráfico")
):
    """Obtener un gráfico específico"""
    try:
        personalizaciones = {}
        if personalizar:
            personalizaciones = {
                "mostrar_valores": True,
                "animaciones": True,
                "interactivo": True
            }
        
        grafico = await service.obtener_grafico(grafico_id, personalizaciones)
        if not grafico:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gráfico '{grafico_id}' no encontrado"
            )
        return grafico
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo gráfico: {str(e)}"
        )

@router.post("/graficos/personalizar", response_model=GraficoMetrica)
async def crear_grafico_personalizado(
    tipo: TipoGrafico,
    datos: List[dict],
    configuracion: dict
):
    """Crear gráfico personalizado"""
    try:
        return await service.generar_grafico_personalizado(tipo, datos, configuracion)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creando gráfico: {str(e)}"
        )

# ========== SERIES TEMPORALES ==========
@router.get("/series/{metrica_id}", response_model=SerieTemporalCompleta)
async def obtener_serie_temporal(
    metrica_id: str,
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None),
    prediccion: bool = Query(False, description="Incluir predicción")
):
    """Obtener serie temporal de una métrica"""
    try:
        # Si no se especifican fechas, usar último mes
        if not fecha_inicio:
            fecha_inicio = datetime.utcnow() - timedelta(days=30)
        if not fecha_fin:
            fecha_fin = datetime.utcnow()
        
        if fecha_inicio >= fecha_fin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fecha de inicio debe ser anterior a fecha de fin"
            )
        
        serie = await service.obtener_serie_temporal(
            metrica_id, fecha_inicio, fecha_fin, prediccion
        )
        if not serie:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron datos para la métrica '{metrica_id}'"
            )
        
        return serie
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo serie temporal: {str(e)}"
        )

# ========== ANÁLISIS COMPARATIVO ==========
@router.get("/comparar/{periodo1}/{periodo2}", response_model=AnalisisComparativo)
async def comparar_metricas(
    periodo1: Periodo,
    periodo2: Periodo
):
    """Comparar métricas entre dos períodos"""
    try:
        return await service.obtener_analisis_comparativo(periodo1, periodo2)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error comparando métricas: {str(e)}"
        )

# ========== ALERTAS ==========
@router.get("/alertas/todas", response_model=List[AlertaMetrica])
async def obtener_todas_alertas():
    """Obtener todas las alertas de métricas"""
    try:
        return await service.obtener_alertas()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo alertas: {str(e)}"
        )

@router.get("/alertas/activas", response_model=List[AlertaMetrica])
async def obtener_alertas_activas(
    severidad: Optional[str] = Query(None, description="Filtrar por severidad")
):
    """Obtener alertas activas"""
    try:
        return await service.obtener_alertas(severidad, "activa")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo alertas activas: {str(e)}"
        )

# ========== TENDENCIAS ==========
@router.post("/tendencias/calcular")
async def calcular_tendencia(
    datos: List[float],
    periodo: int = Query(7, ge=1, le=365)
):
    """Calcular tendencia de una serie de datos"""
    try:
        if len(datos) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requieren al menos 2 puntos de datos"
            )
        
        tendencia = await service.calcular_tendencia(datos, periodo)
        return {
            "datos_entrada": datos,
            "analisis_tendencia": tendencia,
            "recomendacion": await service._generar_recomendacion(tendencia)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error calculando tendencia: {str(e)}"
        )

# ========== CONFIGURACIÓN ==========
@router.post("/configurar")
async def configurar_dashboard(configuracion: ConfiguracionDashboard):
    """Configurar el dashboard de métricas"""
    try:
        # En una implementación real, guardarías esta configuración
        return {
            "mensaje": "Configuración guardada exitosamente",
            "configuracion": configuracion.dict(),
            "fecha_actualizacion": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error configurando dashboard: {str(e)}"
        )

# ========== ESTADÍSTICAS RÁPIDAS ==========
@router.get("/estadisticas/rapidas")
async def obtener_estadisticas_rapidas():
    """Obtener estadísticas rápidas del sistema"""
    try:
        dashboard = await service.obtener_dashboard()
        
        return {
            "total_metricas": len(dashboard.metricas_resumen),
            "total_graficos": len(dashboard.graficos),
            "total_kpis": len(dashboard.kpis),
            "metricas_ascendentes": sum(
                1 for m in dashboard.metricas_resumen 
                if m.tendencia.value == "ascendente"
            ),
            "metricas_descendentes": sum(
                1 for m in dashboard.metricas_resumen 
                if m.tendencia.value == "descendente"
            ),
            "ultima_actualizacion": dashboard.fecha_actualizacion,
            "alertas_activas": len(await service.obtener_alertas(estado="activa")),
            "rendimiento_promedio": 85.6  # Ejemplo
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )