# reportes/models.py
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class TipoReporteEnum(enum.Enum):
    VENTAS = "ventas"
    USUARIOS = "usuarios"
    INVENTARIO = "inventario"
    MARKETING = "marketing"
    FINANCIERO = "financiero"
    SERVICIO = "servicio"

class EstadoReporteEnum(enum.Enum):
    PENDIENTE = "pendiente"
    GENERANDO = "generando"
    COMPLETADO = "completado"
    ERROR = "error"

class FormatoExportacionEnum(enum.Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"

class ReporteModel(Base):
    __tablename__ = "reportes"
    
    id = Column(String, primary_key=True, index=True)
    nombre = Column(String, nullable=False, index=True)
    tipo = Column(Enum(TipoReporteEnum), nullable=False)
    descripcion = Column(String, nullable=True)
    estado = Column(Enum(EstadoReporteEnum), default=EstadoReporteEnum.PENDIENTE)
    formato_salida = Column(Enum(FormatoExportacionEnum), default=FormatoExportacionEnum.PDF)
    filtros = Column(JSON, nullable=True)
    usuario_id = Column(String, nullable=True, index=True)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, onupdate=func.now())
    fecha_completado = Column(DateTime, nullable=True)
    descargas = Column(Integer, default=0)
    url_descarga = Column(String, nullable=True)
    tamaño_archivo = Column(Float, nullable=True)  # MB
    duracion_generacion = Column(Float, nullable=True)  # segundos
    error_mensaje = Column(String, nullable=True)