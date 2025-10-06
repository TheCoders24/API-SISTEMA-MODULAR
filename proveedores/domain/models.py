from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ...database.base import Base

class Proveedores(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    contacto = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)