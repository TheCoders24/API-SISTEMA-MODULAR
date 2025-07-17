# domain/models.py
# importamos las librerias necesarias para el funcionamiento
from sqlalchemy import Column,Integer,String
from ...database.base import Base
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


    
class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, nullable=False)  

class CategoriaBase(BaseModel):
    nombre: str

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaOut(CategoriaBase):
    id: int
    
    class Config:
        from_attributes = True
