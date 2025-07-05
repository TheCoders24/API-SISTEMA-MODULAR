from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from ..Api_Keys_Session.services.api_key_service import create_api_key
from ..Api_Keys_Session.schemas.api_keys_schemas import APIkeyCreate, APIkeyResponse
from datetime import timedelta
from typing import Annotated
from ..database.session import get_db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

from .schemas import UsuarioResponseWithAPIKey


from .schemas import (
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
    Token,
    UsuarioLogin
)
from .auth import (
    get_current_user,
    create_access_token,
    authenticate_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

#router = APIRouter(prefix="/auth", tags=["auth"])
router = APIRouter(prefix="/auth", tags=["auth"])

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        text("SELECT * FROM usuarios WHERE email = :email"),
        {"email": email}
    )
    return result.fetchone()



# Routes
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
            text("""
                INSERT INTO usuarios (nombre, email, password)
                VALUES (:nombre, :email, :password)
                RETURNING id, nombre, email, fecha_registro
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
        api_key_response = await create_api_key(api_key_data)  # ← dict esperado

        # 5. Preparar respuesta
        user_dict = dict(new_user._mapping)
        try:
            user_dict["api_key"] = api_key_response["raw_key"]
        except KeyError:
            raise HTTPException(status_code=500, detail="No se pudo generar la API Key")

        return user_dict

    except Exception as e:
        logger.exception("Error al registrar usuario")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: UsuarioLogin = Body(...),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, form_data.email, form_data.password.get_secret_value())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UsuarioResponse)
async def read_current_user(
    current_user: UsuarioResponse = Depends(get_current_user)
):
    return current_user

@router.patch("/me", response_model=UsuarioResponse)
async def update_current_user(
    user_data: UsuarioUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
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
    
    result = await db.execute(
        f"""
        UPDATE usuarios
        SET {set_clause}
        WHERE email = :email
        RETURNING id, nombre, email, fecha_registro
        """,
        {"email": current_user.email, **update_data}
    )
    updated_user = result.fetchone()
    await db.commit()
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return updated_user