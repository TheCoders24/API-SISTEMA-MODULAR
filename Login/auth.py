from datetime import datetime, timedelta
from typing import Optional, Annotated

import os
import uuid
import logging

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr

from ..database.session import get_db

# -------------------------------------------------
# CONFIGURACIÓN GENERAL
# -------------------------------------------------
load_dotenv()
logger = logging.getLogger(__name__)

ENV = os.getenv("ENV", "development").lower()

ALGORITHM = os.getenv("ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "inventory-api")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "inventory-client")


# -------------------------------------------------
# SECRETOS (CRÍTICO)
# -------------------------------------------------
def get_secret_key() -> str:
    """
    Obtiene la clave secreta según el entorno.
    En producción, si no existe, el sistema NO arranca.
    """
    if ENV == "development":
        return os.getenv("DEV_SECRET", "dev-secret-only-local")

    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("❌ SECRET_KEY no configurada en producción")

    return secret


# -------------------------------------------------
# EXPIRACIÓN DE TOKENS
# -------------------------------------------------
def get_token_expiration_minutes() -> int:
    """
    DEV  -> tokens largos (comodidad)
    PROD -> tokens cortos (seguridad)
    """
    return 1440 if ENV == "development" else 15


# -------------------------------------------------
# SEGURIDAD
# -------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login"
)


# -------------------------------------------------
# MODELOS DE RESPUESTA
# -------------------------------------------------
class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    activo: bool


# -------------------------------------------------
# UTILIDADES DE CONTRASEÑA
# -------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# -------------------------------------------------
# AUTENTICACIÓN DEL USUARIO
# -------------------------------------------------
async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> Optional[dict]:
    try:
        result = await db.execute(
            sa.text("""
                SELECT id, nombre, email, password, is_active
                FROM usuarios
                WHERE email = :email
            """),
            {"email": email.lower().strip()}
        )

        user = result.mappings().first()
        if not user:
            return None

        user_dict = dict(user)

        if not verify_password(password, user_dict["password"]):
            return None

        user_dict.pop("password", None)
        return user_dict

    except Exception as e:
        logger.error("Error en authenticate_user", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la autenticación"
        )


# -------------------------------------------------
# CREACIÓN DEL JWT
# -------------------------------------------------
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()

    now = datetime.utcnow()
    expire = now + (
        expires_delta or timedelta(minutes=get_token_expiration_minutes())
    )

    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "jti": str(uuid.uuid4()),
        "env": ENV
    })

    return jwt.encode(
        to_encode,
        get_secret_key(),
        algorithm=ALGORITHM
    )


# -------------------------------------------------
# VALIDACIÓN DEL PAYLOAD JWT
# -------------------------------------------------
async def validate_token_payload(payload: dict) -> dict:
    required_fields = {
        "sub",
        "email",
        "nombre",
        "is_active",
        "env",
        "iss",
        "aud",
        "jti"
    }

    if not required_fields.issubset(payload):
        logger.error(f"JWT inválido (estructura): {payload}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    if payload["env"] != ENV:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no válido para este entorno"
        )

    if payload["iss"] != JWT_ISSUER or payload["aud"] != JWT_AUDIENCE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token emitido por fuente no confiable"
        )

    payload["id"] = payload["sub"]
    payload["activo"] = payload["is_active"]

    return payload


# -------------------------------------------------
# DEPENDENCIAS DE AUTENTICACIÓN
# -------------------------------------------------
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> dict:
    try:
        payload = jwt.decode(
            token,
            get_secret_key(),
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER
        )
        return await validate_token_payload(payload)

    except JWTError as e:
        logger.warning(f"JWT inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    if not current_user.get("activo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user
