from sqlalchemy import Column, Integer, String, Float, Text
from ..database.base import Base

class Producto(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)  # Unique añadido
    precio = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    descripcion = Column(Text, nullable=True)  # PostgreSQL maneja Text eficientemente