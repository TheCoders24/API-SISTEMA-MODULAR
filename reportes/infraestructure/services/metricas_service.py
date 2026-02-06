import random
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional, Any
from ...application.use_cases.metricas_use_cases import (
    ObtenerDashboardUseCase, ObtenerMetricasRealtimeUseCase,
    ObtenerHistoricoUseCase, CrearKPIConfigUseCase
)
from ...infraestructure.repositories.metricas_repository_imp import MetricasRepositoryImpl

class MetricasService:
    def __init__(self):
        self.metricas_repository = MetricasRepositoryImpl()
        self.obtener_dashboard_uc = ObtenerDashboardUseCase(self.metricas_repository)
        self.obtener_realtime_uc = ObtenerMetricasRealtimeUseCase(self.metricas_repository)
        self.obtener_historico_uc = ObtenerHistoricoUseCase(self.metricas_repository)
        self.crear_kpi_config_uc = CrearKPIConfigUseCase(self.metricas_repository)
    
    async def obtener_dashboard(self, periodo: str, usuario_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtener dashboard de métricas"""
        from ...domain.entities.metricas import Periodo
        
        periodo_enum = Periodo(periodo)
        dashboard = await self.obtener_dashboard_uc.execute(periodo_enum, usuario_id)
        
        # Convertir a dict para la API
        return {
            "id": dashboard.id,
            "nombre": dashboard.nombre,
            "metricas_resumen": [
                {
                    "id": m.id,
                    "nombre": m.nombre,
                    "valor": m.valor,
                    "cambio": m.cambio,
                    "tendencia": m.tendencia.value,
                    "icono": m.icono,
                    "color": m.color,
                    "categoria": m.categoria
                }
                for m in dashboard.metricas_resumen
            ],
            "metricas_detalle": [
                {
                    "id": m.id,
                    "nombre": m.nombre,
                    "valor_actual": m.valor_actual,
                    "cambio_porcentual": m.cambio_porcentual,
                    "unidad": m.unidad,
                    "meta": m.meta,
                    "progreso_meta": m.progreso_meta
                }
                for m in dashboard.metricas_detalle
            ],
            "graficos": [
                {
                    "id": g.id,
                    "titulo": g.titulo,
                    "tipo": g.tipo,
                    "series": g.series
                }
                for g in dashboard.graficos
            ],
            "kpis": [
                {
                    "id": k.id,
                    "nombre": k.nombre,
                    "valor": k.valor,
                    "unidad": k.unidad,
                    "objetivo": k.objetivo,
                    "progreso": k.progreso,
                    "estado": k.estado
                }
                for k in dashboard.kpis
            ],
            "fecha_actualizacion": dashboard.fecha_actualizacion.isoformat(),
            "analisis_insights": [
                {
                    "tipo": i.tipo,
                    "titulo": i.titulo,
                    "descripcion": i.descripcion,
                    "impacto": i.impacto
                }
                for i in dashboard.analisis_insights
            ]
        }
    
    async def obtener_metricas_realtime(self) -> Dict[str, Any]:
        """Obtener métricas en tiempo real"""
        realtime = await self.obtener_realtime_uc.execute()
        
        return {
            "usuarios_conectados": realtime.usuarios_conectados,
            "pedidos_pendientes": realtime.pedidos_pendientes,
            "tickets_soporte": realtime.tickets_soporte,
            "tiempo_respuesta": realtime.tiempo_respuesta,
            "timestamp": realtime.timestamp.isoformat()
        }
    
    async def obtener_metricas_historicas(self, metrica_id: str, dias: int = 7) -> List[Dict[str, Any]]:
        """Obtener datos históricos de una métrica"""
        historicos = await self.obtener_historico_uc.execute(metrica_id, dias)
        
        return [
            {
                "fecha": h.fecha,
                "valor": h.valor,
                "cambio": h.cambio,
                "meta": h.meta
            }
            for h in historicos
        ]
    
    async def crear_kpi_config(self, nombre: str, metrica_id: str, objetivo: float, unidad: str) -> Dict[str, Any]:
        """Crear configuración de KPI"""
        return await self.crear_kpi_config_uc.execute(nombre, metrica_id, objetivo, unidad)