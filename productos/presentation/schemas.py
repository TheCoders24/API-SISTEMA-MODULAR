from pydantic import BaseModel, Field, validator
from typing import Optional

class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, example="Teclado mecánico", description="Nombre del producto")
    descripcion: Optional[str] = Field(None, max_length=500, example="Teclado con switches azules", description="Descripción detallada del producto")
    precio: float = Field(..., gt=0, example=59.99, description="Precio en dólares")
    stock: int = Field(..., ge=0, example=10, description="Cantidad disponible en inventario")
    categoria_id: int = Field(..., example=1, description="ID de la categoría asociada")
    proveedor_id: int = Field(..., example=1, description="ID del proveedor asociado")

    @validator('nombre')
    def validar_nombre(cls, value):
        if value.strip() == '':
            raise ValueError("El nombre no puede estar vacío")
        return value.strip()

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100, example="Teclado mecánico actualizado")
    descripcion: Optional[str] = Field(None, max_length=500)
    precio: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    categoria_id: Optional[int] = None
    proveedor_id: Optional[int] = None

class Producto(ProductoBase):
    id: int = Field(..., example=1, description="ID único del producto")

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "nombre": "Teclado mecánico",
                "descripcion": "Teclado con switches azules",
                "precio": 59.99,
                "stock": 10,
                "categoria_id": 1,
                "proveedor_id": 1
            }
        }
