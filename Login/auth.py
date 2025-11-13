from datetime import datetime, timedelta
from typing import Optional, Annotated
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from ..database.session import get_db
import os
from dotenv import load_dotenv
import uuid
import logging
from pydantic import BaseModel, EmailStr

# -------------------------------------------------
# CONFIGURACIÓN Y MODELOS
# -------------------------------------------------
logger = logging.getLogger(__name__)
load_dotenv()

# 🔹 Entorno actual
ENV = os.getenv("ENV", "production")

# 🔹 Secret por entorno
DEV_SECRET = os.getenv("DEV_SECRET", "clave_dev_segura_" + os.urandom(16).hex())
PROD_SECRET = os.getenv("SECRET_KEY", os.urandom(32).hex())
SECRET_KEY = DEV_SECRET if ENV == "development" else PROD_SECRET

# 🔹 Algoritmo JWT
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# 🔹 Duración del token por entorno
DEV_TOKEN_LIFETIME = int(os.getenv("DEV_TOKEN_LIFETIME", 30))   # minutos
PROD_TOKEN_LIFETIME = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
ACCESS_TOKEN_EXPIRE_MINUTES = DEV_TOKEN_LIFETIME if ENV == "development" else PROD_TOKEN_LIFETIME

# 🔹 Seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# -------------------------------------------------
# MODELO DE RESPUESTA
# -------------------------------------------------
class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    activo: bool


# -------------------------------------------------
# UTILIDADES DE SEGURIDAD
# -------------------------------------------------
def get_actual_secret() -> str:
    return DEV_SECRET if ENV == "development" else SECRET_KEY


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# 🔐 Autenticación del usuario
async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[dict]:
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

        # Validar contraseña
        if not verify_password(password, user_dict["password"]):
            return None

        # Eliminar el hash antes de devolver al usuario
        user_dict.pop("password", None)
        return user_dict

    except Exception as e:
        logger.error(f"Error en authenticate_user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la autenticación"
        )


# 🔐 Creación del token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire

    # Campos adicionales
    to_encode.setdefault("jti", str(uuid.uuid4()))
    to_encode.setdefault("env", ENV)

    return jwt.encode(to_encode, get_actual_secret(), algorithm=ALGORITHM)


# -------------------------------------------------
# VALIDACIÓN DEL PAYLOAD JWT
# -------------------------------------------------
async def validate_token_payload(payload: dict) -> dict:
    """
    Valida que el token tenga todos los campos esperados
    y estandariza la estructura.
    """
    payload["id"] = payload.get("sub")  # normalizar id

    required_fields = ["sub", "id", "email", "nombre", "is_active", "env"]
    if not all(field in payload for field in required_fields):
        logger.error(f"Token con campos faltantes: {payload}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: estructura incorrecta"
        )

    # Validar entorno
    if payload["env"] != ENV:
        logger.error(f"Entorno del token NO coincide: {payload['env']} vs {ENV}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no válido para este entorno"
        )

    # Establecer alias estándar
    payload["activo"] = payload["is_active"]

    # Warning de token de producción en dev
    if ENV == "development" and payload["env"] == "production":
        logger.warning("⚠ TOKEN DE PRODUCCIÓN DETECTADO EN DESARROLLO")

    return payload


# -------------------------------------------------
# DEPENDENCIAS DE AUTENTICACIÓN
# -------------------------------------------------
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            get_actual_secret(),
            algorithms=[ALGORITHM],
            options={"verify_exp": True}
        )

        return await validate_token_payload(payload)

    except JWTError:
        logger.error("Error al decodificar token")
        raise credentials_exception


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    if not current_user.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    return current_user
