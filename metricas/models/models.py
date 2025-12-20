# metricas/ models / models.py
# ==== Importamos Librerias a Utilizar ====
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime  import datetime
from enum import Enum

# ==== ENUMS ====
class Periodo(str, Enum):
    DIARIO = "diario"
    SEMANAL = "semanal"
    MENSUAL = "mensual"
    ANUAL = "anual"
    PERSONALIZADO = "personalizado"

class TipooMetrica(str, Enum):
    VENTAS = "ventas"
    USUARIOS = "usuarios"
    CONVERSION = "conversion"
    PEDIDOS = "pedidos"
    INGRESOS = "ingresos"
    GASTOS = "gastos"
    RETENCION = "retencion"
    SATISFACCION = "satisfacion"

class Tendencia(str, Enum):
    ASCENDENTE = "ascendente"
    DESCENDENTE = "descendente"
    ESTABLE = "estable"

class TipoGrafico(str, Enum):
    LINEA = "linea"
    BARRA = "barra"
    PASTEL = "pastel"
    AREA = "area"
    DISPERSION = "dispersion"

# ========== SCHEMAS PARA REQUEST ==========
class FiltroMetricas(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    categorias: Optional[List[str]] = None
    periodo: Periodo = Periodo.DIARIO
    metricas: List[TipooMetrica] = Field(default_factory=lambda: [
        TipooMetrica.VENTAS, 
        TipooMetrica.USUARIOS, 
        TipooMetrica.CONVERSION
    ])
    agrupacion: Optional[str] = "dia"  # dia, semana, mes, año

class ConfiguracionDashboard(BaseModel):
    layout: Dict[str, Any] = Field(default_factory=dict)
    metricas_visibles: List[str] = []
    tema: str = "claro"
    actualizacion_automatica: bool = True
    intervalo_actualizacion: int = 300  # segundos

# ========== SCHEMAS PARA RESPONSE ==========
class MetricaResumen(BaseModel):
    id: str
    nombre: str
    valor: str
    cambio: str
    tendencia: Tendencia
    icono: str
    color: str
    categoria: str
    descripcion: Optional[str] = None

class MetricaDetalle(BaseModel):
    id: str
    nombre: str
    valor_actual: float
    valor_anterior: float
    cambio_porcentual: float
    tendencia: Tendencia
    unidad: str
    meta: Optional[float] = None
    progreso_meta: Optional[float] = None
    periodo_comparacion: str
    confianza: float = 0.95  # 0-1
    datos_historicos: List[Dict[str, Any]] = Field(default_factory=list)

class PuntoGrafico(BaseModel):
    x: Any  # Puede ser datetime, string, number
    y: float
    etiqueta: Optional[str] = None
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SerieGrafico(BaseModel):
    nombre: str
    datos: List[PuntoGrafico]
    color: str
    tipo: TipoGrafico = TipoGrafico.LINEA
    relleno: bool = False

class GraficoMetrica(BaseModel):
    id: str
    titulo: str
    subtitulo: Optional[str] = None
    series: List[SerieGrafico]
    tipo: TipoGrafico
    configuracion: Dict[str, Any] = Field(default_factory=dict)
    intervalos_x: Optional[List[str]] = None
    intervalos_y: Optional[List[float]] = None

class KPIDashboard(BaseModel):
    id: str
    nombre: str
    valor: float
    unidad: str
    objetivo: float
    progreso: float
    estado: str  # excelente, bueno, regular, critico
    tendencia: Tendencia
    alertas: List[Dict[str, Any]] = Field(default_factory=list)

class DashboardCompleto(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str] = None
    metricas_resumen: List[MetricaResumen]
    metricas_detalle: List[MetricaDetalle]
    graficos: List[GraficoMetrica]
    kpis: List[KPIDashboard]
    periodo: Periodo
    fecha_actualizacion: datetime
    configuracion: ConfiguracionDashboard
    analisis_insights: List[Dict[str, Any]] = Field(default_factory=list)

class AnalisisComparativo(BaseModel):
    periodo_actual: Dict[str, Any]
    periodo_anterior: Dict[str, Any]
    comparativa: Dict[str, Dict[str, float]]
    metricas_mejoradas: List[str]
    metricas_empeoradas: List[str]
    recomendaciones: List[Dict[str, Any]]

class AlertaMetrica(BaseModel):
    id: str
    tipo: str  # critico, advertencia, informativo
    titulo: str
    descripcion: str
    metrica_id: str
    valor_actual: float
    valor_umbral: float
    severidad: str  # alta, media, baja
    fecha_deteccion: datetime
    fecha_resolucion: Optional[datetime] = None
    estado: str  # activa, resuelta, descartada
    accion_recomendada: Optional[str] = None

class SerieTemporalCompleta(BaseModel):
    metrica_id: str
    nombre: str
    datos: List[PuntoGrafico]
    estadisticas: Dict[str, float]
    tendencia: Dict[str, Any]
    prediccion: Optional[List[PuntoGrafico]] = None


