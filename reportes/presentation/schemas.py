# reportes/presentation/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class TipoReporte(str, Enum):
    VENTAS = "ventas"
    USUARIOS = "usuarios"
    INVENTARIO = "inventario"
    MARKETING = "marketing"
    FINANCIERO = "financiero"
    SERVICIO = "servicio"

class EstadoReporte(str, Enum):
    PENDIENTE = "pendiente"
    GENERANDO = "generando"
    COMPLETADO = "completado"
    ERROR = "error"

class FormatoExportacion(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"

class FiltroReporteSchema(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    categorias: Optional[List[str]] = None
    metricas: Optional[List[str]] = None
    intervalo: str = "diario"

class ReporteCreateSchema(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    tipo: TipoReporte
    descripcion: Optional[str] = None
    filtros: Optional[FiltroReporteSchema] = None
    formato_salida: FormatoExportacion = FormatoExportacion.PDF

class ReporteUpdateSchema(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = None

class ReporteResponseSchema(BaseModel):
    id: str
    nombre: str
    tipo: TipoReporte
    descripcion: Optional[str]
    estado: EstadoReporte
    formato_salida: FormatoExportacion
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime]
    fecha_completado: Optional[datetime]
    descargas: int
    url_descarga: Optional[str]
    tamaño_archivo: Optional[float]
    duracion_generacion: Optional[float]
    error_mensaje: Optional[str]
    
    class Config:
        from_attributes = True

class ReporteListResponseSchema(BaseModel):
    reportes: List[ReporteResponseSchema]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int

class ExportacionRequestSchema(BaseModel):
    formato: FormatoExportacion = FormatoExportacion.PDF

class EstadisticasResponseSchema(BaseModel):
    total_reportes: int
    reportes_completados: int
    reportes_generando: int
    reportes_pendientes: int
    descargas_totales: int
    tamaño_total_archivos: float
    reportes_por_tipo: Dict[str, int]
    reportes_mas_descargados: List[Dict[str, Any]]