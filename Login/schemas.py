from pydantic import BaseModel, EmailStr, Field, SecretStr
from datetime import datetime
from typing import Optional
from ..Api_Keys_Session.schemas.api_keys_schemas import APIkeyResponse

# Esquema base  para la parte de Usuario
class UsuarioBase(BaseModel):
    nombre: str = Field(..., max_length=100, examples="Juan Perez")
    email: EmailStr = Field(..., min_length=8, examples="Ejemplo@example.com")

# Esquema para respuesta de usuario (sin datos)
class UsuarioResponse(UsuarioBase):
    id: int
    fecha_registro: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

# Esquema combinado que incluye API Key
class UsuarioResponseWithAPIKey(UsuarioResponse):
    api_key: APIkeyResponse

# Esquema para Creación de Usuario (registro)
class UsuarioCreate(UsuarioBase):
    password: SecretStr = Field(..., min_length=8, examples="Password")

    class config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

# Esquema para login
class UsuarioLogin(BaseModel):
    email: EmailStr = Field(..., example="juan@example.com")
    password: SecretStr = Field(..., example="passwordSegura123")

# Esquema para token JWT
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Esquema para datos del token
class TokenData(BaseModel):
    email: Optional[str] = None

# Esquema para actualización de usuario
class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100, example="Juan Pérez Modificado")
    email: Optional[EmailStr] = Field(None, example="nuevo@example.com")
    password: Optional[SecretStr] = Field(None, min_length=8, example="NuevaPassword123")
