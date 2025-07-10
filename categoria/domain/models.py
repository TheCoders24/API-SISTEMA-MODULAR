# domain/models.py
# importamos las librerias necesarias para el funcionamiento
from sqlalchemy import Column,Integer,String
from ...database.base import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)  