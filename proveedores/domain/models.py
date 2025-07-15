from sqlalchemy import Column,Integer,String
from ...database.base import Base

class Proveedores(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)
    