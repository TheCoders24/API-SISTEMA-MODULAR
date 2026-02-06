from sqlalchemy import Column, String, Float, Integer, DateTime, Enum, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()

class MetricasHistoricasDB(Base):
    __tablename__ = "metricas_historicas"
    
    id = Column(Integer, primary_key=True, index=True)
    metrica_id = Column(String, index=True, nullable=False)
    fecha = Column(DateTime, nullable=False)
    valor = Column(Float, nullable=False)
    cambio = Column(Float, default=0.0)
    meta = Column(Float, nullable=True)
    unidad = Column(String, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DashboardConfigDB(Base):
    __tablename__ = "dashboard_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    usuario_id = Column(String, index=True, nullable=True)
    configuracion = Column(JSON, default=dict)
    es_publico = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class KPIConfigDB(Base):
    __tablename__ = "kpi_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    metrica_id = Column(String, index=True, nullable=False)
    objetivo = Column(Float, nullable=False)
    unidad = Column(String, nullable=False)
    color = Column(String, default="#3B82F6")
    prioridad = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)