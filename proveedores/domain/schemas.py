from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ProveedorBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del proveedor")
    contacto: Optional[str] = Field(None, max_length=100, description="Persona de contacto")
    telefono: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto")
    email: Optional[EmailStr] = Field(None, description="Email de contacto")

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    contacto: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None)

class ProveedorOut(ProveedorBase):
    id: int
    
    class Config:
        from_attributes = True