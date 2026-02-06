from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from ...domain.entities.metricas import Periodo, Tendencia

class MetricaResumenResponse(BaseModel):
    id: str
    nombre: str
    valor: str
    cambio: str
    tendencia: Tendencia
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

class GraficoResponse(BaseModel):
    id: str
    titulo: str
    tipo: str
    series: List[Dict[str, Any]]

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
    graficos: List[GraficoResponse]
    kpis: List[KPIResponse]
    fecha_actualizacion: datetime
    analisis_insights: List[InsightResponse]

class RealtimeMetricsResponse(BaseModel):
    usuarios_conectados: int
    pedidos_pendientes: int
    tickets_soporte: int
    tiempo_respuesta: float
    timestamp: datetime

class HistoricoResponse(BaseModel):
    metrica_id: str
    datos: List[Dict[str, Any]]
    dias: int

class KPICreateRequest(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    metrica_id: str = Field(...)
    objetivo: float = Field(..., gt=0)
    unidad: str = Field(..., min_length=1, max_length=20)