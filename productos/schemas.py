from pydantic import BaseModel, Field
from typing import Optional

class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str]
    precio: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    categoria_id: int
    proveedor_id: int
    usuario_id: int

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: int

    class Config:
        orm_mode = True
