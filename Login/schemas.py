# login/schemas.py

from pydantic import BaseModel, EmailStr, Field, SecretStr
from typing import Optional


# ───────────────────────────────────────────────
# API KEY (alineado con Api_keys_Session)
# ───────────────────────────────────────────────

class APIKeyCreate(BaseModel):
    user_id: str


class APIKeyResponse(BaseModel):
    raw_key: str
    user_id: str


# ─────────────────────────────
# USUARIO BASE / REGISTRO
# ─────────────────────────────

class UsuarioBase(BaseModel):
    nombre: str = Field(
        ...,
        max_length=100,
        examples=["Juan Pérez"]
    )
    email: EmailStr = Field(
        ...,
        examples=["ejemplo@example.com"]
    )


class UsuarioCreate(UsuarioBase):
    password: SecretStr = Field(
        ...,
        min_length=8,
        examples=["PasswordSegura123"]
    )


# ─────────────────────────────
# LOGIN
# ─────────────────────────────

class UsuarioLogin(BaseModel):
    email: EmailStr = Field(
        ...,
        examples=["juan@example.com"]
    )
    password: SecretStr = Field(
        ...,
        examples=["PasswordSegura123"]
    )


# ─────────────────────────────
# RESPUESTAS DE USUARIO
# ─────────────────────────────

class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool

    model_config = {
        "from_attributes": True
    }


class UsuarioResponseWithAPIKey(UsuarioResponse):
    api_key: str


# ─────────────────────────────
# JWT
# ─────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─────────────────────────────
# ACTUALIZACIÓN DE USUARIO
# ─────────────────────────────

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(
        None,
        max_length=100,
        examples=["Juan Pérez Modificado"]
    )
    password: Optional[SecretStr] = Field(
        None,
        min_length=8,
        examples=["NuevaPassword123"]
    )
