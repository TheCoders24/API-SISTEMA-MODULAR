#login/auth.py

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

# Cargar variables de entorno
load_dotenv()

# Configuración desde variables de entorno
SECRET_KEY = os.getenv("SECRET_KEY", "asdasdasdasdsadsadasdsasdasda")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "300"))

# Configuración de seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash almacenado"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash seguro de la contraseña"""
    return pwd_context.hash(password)

async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> Optional[dict]:
    try:
        # Obtener todos los campos necesarios para el token
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

        hashed_password = user.get("password")
        if not hashed_password:
            return None
        
        if not verify_password(password, hashed_password):
            return None

        # Convertir a diccionario y eliminar la contraseña
        user_dict = dict(user)
        user_dict.pop("password", None)  # Eliminar contraseña por seguridad
        return user_dict

    except Exception as e:
        print("Error en authenticate_user:", e)
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la autenticación"
        )

def create_access_token(
    user_data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Genera un token JWT con los datos necesarios del usuario
    
    Args:
        user_data: Datos del usuario (debe contener: id, nombre, email, is_active)
        expires_delta: Tiempo de expiración del token
    
    Returns:
        str: Token JWT firmado
    """
    # Crear payload con datos esenciales
    to_encode = {
        "sub": user_data["email"],  # Subject estándar
        "jti": str(uuid.uuid4()),   # Identificador único para posible revocación
        "id": user_data["id"],
        "nombre": user_data["nombre"],
        "is_active": user_data["is_active"],
    }
    
    # Agregar expiración
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> dict:
    """
    Obtiene el usuario actual basado en el token JWT (sin consultar la base de datos)
    
    Args:
        token: Token JWT
    
    Returns:
        dict: Datos del usuario extraídos del token
    
    Raises:
        HTTPException: Si el token es inválido
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar token con verificación de expiración
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True}  # Verificar expiración
        )
        
        # Verificar campos esenciales
        required_fields = ["sub", "id", "nombre", "is_active"]
        if not all(field in payload for field in required_fields):
            print(f"Faltan campos en el token: {payload}")
            raise credentials_exception
            
        # Renombrar is_active a activo para consistencia
        payload["activo"] = payload["is_active"]
            
        return payload
    except JWTError as e:
        print(f"ERROR DECODIFICANDO TOKEN: {str(e)}")
        print(f"TOKEN RECIBIDO: {token}")
        print(f"SECRET_KEY: {SECRET_KEY}")
        print(f"ALGORITMO: {ALGORITHM}")
        traceback.print_exc()
        raise credentials_exception

async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """
    Verifica que el usuario esté activo
    
    Args:
        current_user: Datos del usuario actual
    
    Returns:
        dict: Datos del usuario si está activo
    
    Raises:
        HTTPException: Si el usuario está inactivo
    """
    if not current_user.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user