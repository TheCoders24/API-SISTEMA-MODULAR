from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class Periodo(str, Enum):
    DIARIO = "diario"
    SEMANAL = "semanal"
    MENSUAL = "mensual"
    ANUAL = "anual"

class Tendencia(str, Enum):
    ASCENDENTE = "ascendente"
    DESCENDENTE = "descendente"
    ESTABLE = "estable"

@dataclass
class MetricaResumen:
    id: str
    nombre: str
    valor: str
    cambio: str
    tendencia: Tendencia
    icono: str
    color: str
    categoria: str

@dataclass
class MetricaDetalle:
    id: str
    nombre: str
    valor_actual: float
    cambio_porcentual: float
    unidad: str
    meta: float
    progreso_meta: float

@dataclass
class SerieGrafico:
    nombre: str
    datos: List[Dict[str, Any]]
    color: str

@dataclass
class Grafico:
    id: str
    titulo: str
    tipo: str
    series: List[SerieGrafico]

@dataclass
class KPI:
    id: str
    nombre: str
    valor: float
    unidad: str
    objetivo: float
    progreso: float
    estado: str

@dataclass
class Insight:
    tipo: str
    titulo: str
    descripcion: str
    impacto: str

@dataclass
class Dashboard:
    id: str
    nombre: str
    metricas_resumen: List[MetricaResumen]
    metricas_detalle: List[MetricaDetalle]
    graficos: List[Grafico]
    kpis: List[KPI]
    fecha_actualizacion: datetime
    analisis_insights: List[Insight]

@dataclass
class DatoHistorico:
    fecha: str
    valor: float
    cambio: float
    meta: Optional[float] = None

@dataclass
class MetricasRealtime:
    usuarios_conectados: int
    pedidos_pendientes: int
    tickets_soporte: int
    tiempo_respuesta: float
    timestamp: datetime