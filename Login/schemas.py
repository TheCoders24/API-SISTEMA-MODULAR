from pydantic import BaseModel, EmailStr, Field, SecretStr
from datetime import datetime
from typing import Optional

# ───────────────────────────────────────────────
# API Key Models
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
    nombre: str = Field(..., max_length=100, examples=["Juan Perez"])
    email: EmailStr = Field(..., min_length=8, examples=["ejemplo@example.com"])

class UsuarioCreate(UsuarioBase):
    password: SecretStr = Field(..., min_length=8, examples=["PasswordSegura123"])

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
    activo: bool  # Campo agregado para el estado de la cuenta
    # fecha_registro: datetime  # Comentado porque no está en el token

    class Config:
        from_attributes = True

class UsuarioResponseWithAPIKey(UsuarioResponse):
    api_key: str

# ─────────────────────────────
# JWT Token
# ─────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ─────────────────────────────
# Usuario Actualización
# ─────────────────────────────

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100, example="Juan Pérez Modificado")
    password: Optional[SecretStr] = Field(None, min_length=8, example="NuevaPassword123")