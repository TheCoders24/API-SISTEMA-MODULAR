# login/routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from datetime import timedelta
from typing import Annotated
import logging

from ..database.session import get_db
from ..Api_keys_Session.domain.entities.repositories.api_keys_repository_impl import MongoAPIKeyRepository
from ..Api_keys_Session.application.service.api_keys_service import CreateAPIKeyUseCase
from ..Api_keys_Session.presentation.schemas.api_keys_schemas import APIKeyCreate
from .auth import (
    ALGORITHM,
    SECRET_KEY,
    get_current_active_user,
    create_access_token,
    authenticate_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from .schemas import (
    UsuarioResponseWithAPIKey,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdate,
    Token,
    UsuarioLogin,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ==============================================================
# FUNCIONES AUXILIARES
# ==============================================================

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


# ==============================================================
# REGISTRO DE USUARIO
# ==============================================================

@router.post(
    "/register",
    response_model=Token,  # 👈 devolvemos el token en lugar del usuario directo
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UsuarioCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1️⃣ Verificar si ya existe
        existing_user = await get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="El email ya está registrado")

        # 2️⃣ Hashear contraseña
        hashed_password = get_password_hash(user_data.password.get_secret_value())

        # 3️⃣ Crear usuario
        result = await db.execute(
            sa.text("""
                INSERT INTO usuarios (nombre, email, password, is_active)
                VALUES (:nombre, :email, :password, TRUE)
                RETURNING id, nombre, email, is_active
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

        # 4️⃣ Crear API Key
        api_key_repository = MongoAPIKeyRepository()
        use_case = CreateAPIKeyUseCase(api_key_repository)
        api_key_response = await use_case.execute(user_id=str(new_user.id))

        # 5️⃣ Crear token JWT
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(new_user.id), "email": new_user.email},
            expires_delta=access_token_expires
        )

        # 6️⃣ Devolver respuesta esperada
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "nombre": new_user.nombre,
                "email": new_user.email,
                "api_key": api_key_response["raw_key"]
            }
        }

    except Exception as e:
        logger.exception("Error al registrar usuario")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==============================================================
# LOGIN DE USUARIO
# ==============================================================

@router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
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

    if "id" not in user or "nombre" not in user or "is_active" not in user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Datos de usuario incompletos"
        )

    # Crear token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user, expires_delta=access_token_expires)

    # Debug del token
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        logger.info(f"Token generado correctamente: {payload}")
    except JWTError as e:
        logger.error(f"Error al decodificar token: {str(e)}")

    # Cookie segura (opcional)
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return {"access_token": access_token, "token_type": "bearer"}


# ==============================================================
# OBTENER USUARIO ACTUAL
# ==============================================================

@router.get("/users", response_model=UsuarioResponse)
async def read_current_user(
    current_user: dict = Depends(get_current_active_user)
):
    logger.debug(f"Usuario autenticado actual: {current_user}")
    return {
        "id": current_user["id"],
        "nombre": current_user["nombre"],
        "email": current_user["sub"],
        "activo": current_user["activo"]
    }


# ==============================================================
# ACTUALIZAR USUARIO
# ==============================================================

@router.patch("/me", response_model=UsuarioResponse)
async def update_current_user(
    user_data: UsuarioUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    update_data = user_data.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"].get_secret_value())

    if not update_data:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")

    set_clause = ", ".join([f"{key} = :{key}" for key in update_data.keys()])

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
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return dict(updated_user._mapping)


# ==============================================================
# OBTENER USUARIO AUTENTICADO (ALIAS)
# ==============================================================

@router.get("/current_user", response_model=UsuarioResponse)
async def read_current_user_alias(
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    return UsuarioResponse(
        id=current_user["id"],
        nombre=current_user["nombre"],
        email=current_user["sub"],
        activo=current_user["activo"],
    )
