from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr

# ELIMINADOS LOS PARÉNTESIS: class Base(DeclarativeBase):
class Base(DeclarativeBase):
    """
    Clase base para el sistema de inventario modular.
    Hereda directamente de la clase DeclarativeBase.
    """
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Genera el nombre de la tabla automáticamente basado en el nombre de la clase"""
        return cls.__name__.lower()


class AuditMixin:
    """Añade control de fechas automático a cualquier tabla"""
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), 
        onupdate=func.now()
    )