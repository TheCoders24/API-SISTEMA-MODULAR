#reporte/domain/entites.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
# import FormatoExportacion

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

@dataclass
class FiltroReporte:
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    categorias: Optional[List[str]] = None
    metricas: Optional[List[str]] = None
    intervalo: str = "diario"

    def to_dict(self) -> dict[str, any]:
        return{
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_final": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "categoria": self.categorias,
            "metricas": self.metricas,
            "intervalo": self.intervalo
        }
@dataclass
class Reporte:
    id: str
    nombre: str
    tipo: TipoReporte
    descripcion: Optional[str] = None
    estado: EstadoReporte = EstadoReporte.PENDIENTE
    formato_salida: FormatoExportacion = FormatoExportacion.PDF
    filtros: Optional[FiltroReporte] = None
    usuario_id: Optional[str] = None
    fecha_creacion: datetime = None
    fecha_actualizacion: Optional[datetime] = None
    fecha_completado: Optional[datetime] = None
    descargas: int = 0
    url_descarga: Optional[str] = None
    tamaño_archivo: Optional[float] = None  # MB
    duracion_generacion: Optional[float] = None  # segundos
    error_mensaje: Optional[str] = None


    def _post_init_(self):
        if self.fecha_creacion is None:
            self.fecha_creacion = datetime.utcnow()
    
    def iniciar_generacion(self):
        self.estado = EstadoReporte.GENERANDO
        self.fecha_actualizacion = datetime.utcnow()

    def completar_generacion(self, url_descarga: str, tamaño_archivo: float, duracion: float):
        self.estado = EstadoReporte.COMPLETADO
        self.url_descarga = url_descarga
        self.tamaño_archivo = tamaño_archivo
        self.duracion_generacion = duracion
        self.fecha_completado = datetime.utcnow()
        self.fecha_actualizacion = datetime.utcnow()

    def marcar_Error(self, mensaje_error):
        self.estado = EstadoReporte.ERROR
        self.error_mensaje = mensaje_error
        self.fecha_actualizacion = datetime.utcnow()

    def incrementar_descargas(self):
        self.descargas += 1
        self.fecha_actualizacion = datetime.utcnow()
    
    def es_descargable(self) -> bool:
        return self.estado == EstadoReporte.COMPLETADO and self.url_descarga is not None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo.value,
            "descripcion": self.descripcion,
            "estado": self.estado.value,
            "formato_salida": self.formato_salida.value,
            "filtros": self.filtros.to_dict() if self.filtros else None,
            "usuario_id": self.usuario_id,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "fecha_actualizacion": self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None,
            "fecha_completado": self.fecha_completado.isoformat() if self.fecha_completado else None,
            "descargas": self.descargas,
            "url_descarga": self.url_descarga,
            "tamaño_archivo": self.tamaño_archivo,
            "duracion_generacion": self.duracion_generacion,
            "error_mensaje": self.error_mensaje
        }

@dataclass
class DatosReporte:
    ventas_totales: Optional[float] = None
    ventas_por_categoria: Optional[Dict[str, float]] = None
    usuarios_nuevos: Optional[int] = None
    usuarios_activos: Optional[int] = None
    tasa_conversion: Optional[float] = None
    pedidos_totales: Optional[int] = None
    metricas_temporales: Optional[Dict[str, List[Dict[str, Any]]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ventas_totales": self.ventas_totales,
            "ventas_por_categoria": self.ventas_por_categoria,
            "usuarios_nuevos": self.usuarios_nuevos,
            "usuarios_activos": self.usuarios_activos,
            "tasa_conversion": self.tasa_conversion,
            "pedidos_totales": self.pedidos_totales,
            "metricas_temporales": self.metricas_temporales
        }