from pydantic import BaseModel

class ProductoBase(BaseModel):
    nombre: str
    precio: float
    stock: int

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: int

    class Config:
        from_attributes = True  # Para ORM