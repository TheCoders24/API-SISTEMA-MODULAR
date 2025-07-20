# login/routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from ..database.session import get_db
import logging
from datetime import timedelta
from typing import Annotated
from jose import jwt, JWTError

# Importaciones de tu auth.py corregido
from .auth import (
    ALGORITHM,
    SECRET_KEY,
    get_current_active_user,
    create_access_token,
    authenticate_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme
)
from .schemas import UsuarioResponseWithAPIKey, UsuarioCreate, UsuarioResponse, UsuarioUpdate, Token, UsuarioLogin
from ..Api_Keys_Session.services.api_key_service import create_api_key
from ..Api_Keys_Session.schemas.api_keys_schemas import APIkeyCreate, APIkeyResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

async def get_user_by_email(db: AsyncSession, email: str):
    """Obtiene un usuario por email con todos los campos necesarios"""
    result = await db.execute(
        sa.text("""
            SELECT id, nombre, email, password, is_active
            FROM usuarios
            WHERE email = :email
        """),
        {"email": email}
    )
    return result.fetchone()

@router.post("/register", response_model=UsuarioResponseWithAPIKey, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UsuarioCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1. Verificar si el usuario ya existe
        existing_user = await get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )

        # 2. Hashear la contraseña
        hashed_password = get_password_hash(user_data.password.get_secret_value())

        # 3. Insertar nuevo usuario
        result = await db.execute(
            sa.text("""
                INSERT INTO usuarios (nombre, email, password)
                VALUES (:nombre, :email, :password)
                RETURNING id, nombre, email
            """),
            {
                "nombre": user_data.nombre,
                "email": user_data.email,
                "password": hashed_password
            }
        )
        new_user = result.fetchone()
        if new_user is None:
            raise HTTPException(status_code=500, detail="No se pudo crear el usuario")
        await db.commit()

        # 4. Crear API Key
        api_key_data = APIkeyCreate(user_id=str(new_user.id))
        api_key_response = await create_api_key(api_key_data)

        # 5. Preparar respuesta
        user_dict = dict(new_user._mapping)
        if "raw_key" in api_key_response:
            user_dict["api_key"] = api_key_response["raw_key"]
        else:
            logger.error("No se pudo generar la API Key")
            raise HTTPException(status_code=500, detail="No se pudo generar la API Key")

        return user_dict

    except Exception as e:
        logger.exception("Error al registrar usuario")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: UsuarioLogin = Body(...),
    db: AsyncSession = Depends(get_db)
):
    # Autenticar usuario con email y contraseña
    user = await authenticate_user(db, form_data.email, form_data.password.get_secret_value())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Asegurarse que tenemos todos los campos necesarios
    if "id" not in user or "nombre" not in user or "is_active" not in user:
        print("Datos de usuario incompletos:", user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Datos de usuario incompletos"
        )
    
    # Crear token de acceso con datos del usuario
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user, expires_delta=access_token_expires)
    
    # Depuración: Verificar que el token se puede decodificar
    try:
        payload = jwt.decode(
            access_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": False}  # Solo para depuración
        )
        print("Token generado correctamente:", payload)
    except JWTError as e:
        print("ERROR en token generado:", str(e))
    
    # Opcional: Guardar token en cookie segura
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users", response_model=UsuarioResponse)
async def read_current_user(
    current_user: dict = Depends(get_current_active_user)
):
    """Endpoint protegido que devuelve datos del usuario actual"""
    return {
        "id": current_user["id"],
        "nombre": current_user["nombre"],
        "email": current_user["sub"],  # 'sub' contiene el email
        "activo": current_user["activo"]
    }

@router.patch("/me", response_model=UsuarioResponse)
async def update_current_user(
    user_data: UsuarioUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualiza los datos del usuario actual"""
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"].get_secret_value())
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron datos para actualizar"
        )
    
    # Construir la consulta dinámicamente
    set_clause = ", ".join([f"{key} = :{key}" for key in update_data.keys()])
    
    # Actualizar usando el ID del usuario del token
    result = await db.execute(
        f"""
        UPDATE usuarios
        SET {set_clause}
        WHERE id = :user_id
        RETURNING id, nombre, email
        """,
        {"user_id": current_user["id"], **update_data}
    )
    updated_user = result.fetchone()
    await db.commit()
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    # Convertir a diccionario y devolver
    return dict(updated_user._mapping)