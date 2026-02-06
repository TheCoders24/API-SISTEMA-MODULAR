# reportes/application/use_cases/metricas_use_cases.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ...domain.entities.metricas import (
    Dashboard, MetricaResumen, MetricaDetalle, Grafico, KPI, Insight,
    MetricasRealtime, DatoHistorico, Periodo, Tendencia
)
from ...domain.repositories.metricas_repository import MetricasRepository

class ObtenerDashboardUseCase:
    def __init__(self, metricas_repository: MetricasRepository):
        self.metricas_repository = metricas_repository
    
    async def execute(self, periodo: Periodo, usuario_id: Optional[str] = None) -> Dashboard:
        """Obtener dashboard de métricas"""
        return await self.metricas_repository.obtener_dashboard(periodo, usuario_id)

class ObtenerMetricasRealtimeUseCase:
    def __init__(self, metricas_repository: MetricasRepository):
        self.metricas_repository = metricas_repository
    
    async def execute(self) -> MetricasRealtime:
        """Obtener métricas en tiempo real"""
        return await self.metricas_repository.obtener_metricas_realtime()

class ObtenerHistoricoUseCase:
    def __init__(self, metricas_repository: MetricasRepository):
        self.metricas_repository = metricas_repository
    
    async def execute(self, metrica_id: str, dias: int = 7) -> List[DatoHistorico]:
        """Obtener datos históricos de una métrica"""
        return await self.metricas_repository.obtener_metricas_historicas(metrica_id, dias)

class CrearKPIConfigUseCase:
    def __init__(self, metricas_repository: MetricasRepository):
        self.metricas_repository = metricas_repository
    
    async def execute(self, nombre: str, metrica_id: str, objetivo: float, unidad: str) -> Dict[str, Any]:
        """Crear configuración de KPI"""
        return await self.metricas_repository.crear_kpi_config(nombre, metrica_id, objetivo, unidad)