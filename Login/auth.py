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
import traceback
import uuid
import logging
from faker import Faker  # Para datos de prueba anónimos

# Configurar logging
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración segura por entorno
ENV = os.getenv("ENV", "production")
SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())  # Valor por defecto seguro
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # Tiempo más corto

# Configuración específica para desarrollo
DEV_SECRET = os.getenv("DEV_SECRET", "clave_dev_segura_" + os.urandom(16).hex())
DEV_TOKEN_LIFETIME = 15  # minutos

# Instancia de Faker para datos anónimos
fake = Faker()

# Configuración de seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_actual_secret() -> str:
    """Devuelve la clave secreta según el entorno"""
    return DEV_SECRET if ENV == "development" else SECRET_KEY

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def anonymize_user_data(user_data: dict) -> dict:
    """Anonimiza datos sensibles del usuario para desarrollo"""
    if ENV != "development":
        return user_data
        
    return {
        "id": f"dev_{user_data['id']}",
        "nombre": f"DEV_{fake.first_name()}",
        "email": f"dev_{user_data['id']}@example.com",
        "is_active": True
    }

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
        hashed_password = user_dict.get("password")
        
        if not hashed_password or not verify_password(password, hashed_password):
            return None

        # Anonimizar en desarrollo
        if ENV == "development":
            user_dict = anonymize_user_data(user_dict)
        
        user_dict.pop("password", None)
        return user_dict

    except Exception as e:
        logger.error(f"Error en authenticate_user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la autenticación"
        )

def create_access_token(
    user_data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    # Configuración específica para desarrollo
    if ENV == "development":
        # Forzar anonimización en dev
        user_data = anonymize_user_data(user_data)
        expires_delta = timedelta(minutes=DEV_TOKEN_LIFETIME)
        logger.warning("TOKEN DE DESARROLLO GENERADO - DATOS ANONIMIZADOS")
    
    # Crear payload con datos esenciales
    to_encode = {
        "sub": user_data["email"],
        "jti": str(uuid.uuid4()),
        "id": user_data["id"],
        "nombre": user_data["nombre"],
        "is_active": user_data["is_active"],
        "env": ENV  # Identificador de entorno
    }
    
    # Tiempo de expiración
    expire = datetime.utcnow() + (
        expires_delta or 
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    
    return jwt.encode(
        to_encode, 
        get_actual_secret(),  # Clave según entorno
        algorithm=ALGORITHM
    )

async def validate_token_payload(payload: dict) -> dict:
    """Valida y normaliza el payload del token"""
    required_fields = ["sub", "id", "nombre", "is_active", "env"]
    if not all(field in payload for field in required_fields):
        logger.error(f"Token con campos faltantes: {payload}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: estructura incorrecta"
        )
    
    # Verificar coincidencia de entorno
    if payload["env"] != ENV:
        logger.error(f"Entorno de token no coincide: {payload['env']} vs {ENV}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no válido para este entorno"
        )
    
    # Renombrar para consistencia
    payload["activo"] = payload["is_active"]
    
    # Advertencia si se usa token de producción en desarrollo
    if ENV == "development" and payload["env"] == "production":
        logger.warning("TOKEN DE PRODUCCIÓN DETECTADO EN DESARROLLO - POSIBLE FALLO DE SEGURIDAD")
    
    return payload

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            get_actual_secret(),  # Clave correcta por entorno
            algorithms=[ALGORITHM],
            options={"verify_exp": True}
        )
        return await validate_token_payload(payload)
        
    except JWTError as e:
        logger.error(f"Error decodificando token: {str(e)}")
        logger.debug(f"Token recibido: {token[:30]}...")
        logger.debug(f"Clave usada: {get_actual_secret()[:6]}...")
        raise credentials_exception

async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    if not current_user.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user

# Función para generar tokens de prueba en desarrollo
async def generate_dev_token(
    db: AsyncSession,
    user_id: Optional[int] = None
) -> str:
    """Genera token seguro para desarrollo sin credenciales reales"""
    if ENV != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo disponible en entorno de desarrollo"
        )
    
    # Crear usuario ficticio
    fake_user = {
        "id": user_id or fake.random_number(digits=5),
        "nombre": fake.name(),
        "email": fake.email(),
        "is_active": True
    }
    
    return create_access_token(fake_user)