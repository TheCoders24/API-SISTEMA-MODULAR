from datetime import datetime, timedelta
from typing import Optional, Annotated
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from ..database import get_db
from .schemas import TokenData
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración desde variables de entorno
SECRET_KEY = os.getenv("SECRET_KEY", "clave_secreta_por_defecto_solo_para_desarrollo")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

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
    """
    Autentica un usuario con email y contraseña
    
    Args:
        db: Sesión de base de datos
        email: Email del usuario
        password: Contraseña en texto plano
    
    Returns:
        dict: Datos del usuario si la autenticación es exitosa
        None: Si la autenticación falla
    """
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
        
        if not user or not verify_password(password, user["password"]):
            return None
            
        return dict(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la autenticación"
        )

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Genera un token JWT
    
    Args:
        data: Datos a incluir en el token
        expires_delta: Tiempo de expiración del token
    
    Returns:
        str: Token JWT firmado
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Obtiene el usuario actual basado en el token JWT
    
    Args:
        token: Token JWT
        db: Sesión de base de datos
    
    Returns:
        dict: Datos del usuario
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    try:
        result = await db.execute(
            sa.text("""
            SELECT id, nombre, email, is_active
            FROM usuarios
            WHERE email = :email
            """),
            {"email": email}
        )
        user = result.mappings().first()
        
        if not user:
            raise credentials_exception
            
        return dict(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el usuario"
        )

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
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user