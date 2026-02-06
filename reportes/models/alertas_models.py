from sqlalchemy import Column, String, Enum, DateTime, Boolean, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()

class AlertaDB(Base):
    __tablename__ = "alertas"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum('advertencia', 'critica', 'informativa', name='tipo_alerta'), nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    metrica_id = Column(String, index=True, nullable=False)
    severidad = Column(Enum('alta', 'media', 'baja', name='severidad_alerta'), nullable=False)
    fecha_deteccion = Column(DateTime, default=datetime.utcnow)
    accion_recomendada = Column(String, nullable=True)
    resuelta = Column(Boolean, default=False)
    fecha_resolucion = Column(DateTime, nullable=True)
    datos_contexto = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)