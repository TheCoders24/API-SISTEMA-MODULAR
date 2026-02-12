from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class LogModel(Base):
    __tablename__ = "observability_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(String, nullable=False, index=True)
    level = Column(String, nullable=False)
    category = Column(String, nullable=False)
    action = Column(String, nullable=False)
    message = Column(String, nullable=False)
    user_id = Column(String, index=True)
    role = Column(String)
    ip = Column(String, index=True)
    endpoint = Column(String)
    
    # 🔥 CAMBIADO: 'metadata' → 'log_metadata' (metadata es palabra reservada)
    log_metadata = Column("metadata", JSON, default={})  # Alias para mantener compatibilidad
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Índices compuestos
    __table_args__ = (
        Index("ix_logs_user_timestamp", "user_id", "timestamp"),
        Index("ix_logs_category_timestamp", "category", "timestamp"),
        Index("ix_logs_ip_timestamp", "ip", "timestamp"),
    )