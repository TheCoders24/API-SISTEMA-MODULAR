from pydantic import BaseModel, EmailStr, Field, SecretStr
from datetime import datetime
from typing import Optional

# ───────────────────────────────────────────────
# API Key Models (si los usas en otros endpoints)
# ───────────────────────────────────────────────

class APIkeyCreate(BaseModel):
    user_id: str

class APIkeyResponse(BaseModel):
    raw_key: str
    user_id: str

# ─────────────────────────────
# Usuario Base / Registro
# ─────────────────────────────

class UsuarioBase(BaseModel):
    nombre: str = Field(..., max_length=100, examples="Juan Perez")
    email: EmailStr = Field(..., min_length=8, examples="Ejemplo@example.com")

class UsuarioCreate(UsuarioBase):
    password: SecretStr = Field(..., min_length=8, examples="Password")

    class config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None
        }

# ─────────────────────────────
# Usuario Login
# ─────────────────────────────

class UsuarioLogin(BaseModel):
    email: EmailStr = Field(..., example="juan@example.com")
    password: SecretStr = Field(..., example="passwordSegura123")

# ─────────────────────────────
# Usuario Respuesta
# ─────────────────────────────

class UsuarioResponse(UsuarioBase):
    id: int
    fecha_registro: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

class UsuarioResponseWithAPIKey(UsuarioResponse):
    api_key: str  # ✅ CORREGIDO: ahora es un string, no un modelo

# ─────────────────────────────
# JWT Token y Datos del Token
# ─────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# ─────────────────────────────
# Usuario Actualización
# ─────────────────────────────

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100, example="Juan Pérez Modificado")
    email: Optional[EmailStr] = Field(None, example="nuevo@example.com")
    password: Optional[SecretStr] = Field(None, min_length=8, example="NuevaPassword123")
