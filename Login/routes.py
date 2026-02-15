# login/routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Body, Response
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from datetime import timedelta
from typing import Annotated
import logging

from ..database.session import get_db

from ..Api_keys_Session.domain.entities.repositories.api_keys_repository_impl import (
    MongoAPIKeyRepository
)
from ..Api_keys_Session.application.service.api_keys_service import (
    CreateAPIKeyUseCase
)
from ..Api_keys_Session.presentation.schemas.api_keys_schemas import (
    APIKeyCreate
)

from .auth import (
    get_current_active_user,
    create_access_token,
    authenticate_user,
    get_password_hash,
    get_token_expiration_minutes,
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
    result = await db.execute(
        sa.text("""
            SELECT id, nombre, email, password, is_active
            FROM usuarios
            WHERE email = :email
        """),
        {"email": email.lower().strip()}
    )
    return result.mappings().first()


# ==============================================================
# REGISTRO DE USUARIO
# ==============================================================

@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UsuarioCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 1️⃣ Verificar existencia
        existing_user = await get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="El email ya está registrado"
            )

        # 2️⃣ Hash de contraseña
        hashed_password = get_password_hash(
            user_data.password.get_secret_value()
        )

        # 3️⃣ Crear usuario
        result = await db.execute(
            sa.text("""
                INSERT INTO usuarios (nombre, email, password, is_active)
                VALUES (:nombre, :email, :password, TRUE)
                RETURNING id, nombre, email, is_active
            """),
            {
                "nombre": user_data.nombre.strip(),
                "email": user_data.email.lower().strip(),
                "password": hashed_password
            }
        )
        new_user = result.mappings().first()
        if not new_user:
            raise HTTPException(
                status_code=500,
                detail="No se pudo crear el usuario"
            )

        await db.commit()

        # 4️⃣ Crear API Key
        api_key_repository = MongoAPIKeyRepository()
        use_case = CreateAPIKeyUseCase(api_key_repository)
        api_key_response = await use_case.execute(
            user_id=str(new_user["id"])
        )

        # 5️⃣ Crear JWT
        access_token = create_access_token(
            data={
                "sub": str(new_user["id"]),
                "email": new_user["email"],
                "nombre": new_user["nombre"],
                "is_active": True
            },
            expires_delta=timedelta(
                minutes=get_token_expiration_minutes()
            )
        )

        # 6️⃣ Respuesta final
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_user["id"],
                "nombre": new_user["nombre"],
                "email": new_user["email"],
                "api_key": api_key_response["raw_key"]
            }
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Error al registrar usuario")
        raise HTTPException(
            status_code=500,
            detail="Error interno al registrar usuario"
        )


# ==============================================================
# LOGIN
# ==============================================================

@router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: UsuarioLogin = Body(...),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(
        db,
        form_data.email,
        form_data.password.get_secret_value()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    access_token = create_access_token(
        data={
            "sub": str(user["id"]),
            "email": user["email"],
            "nombre": user["nombre"],
            "is_active": user["is_active"]
        },
        expires_delta=timedelta(
            minutes=get_token_expiration_minutes()
        )
    )

    # Cookie segura (opcional)
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=get_token_expiration_minutes() * 60
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==============================================================
# USUARIO ACTUAL
# ==============================================================

@router.get("/users", response_model=UsuarioResponse)
async def read_current_user(
    current_user: dict = Depends(get_current_active_user)
):
    return {
        "id": current_user["id"],
        "nombre": current_user["nombre"],
        "email": current_user["email"],
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
        update_data["password"] = get_password_hash(
            update_data["password"].get_secret_value()
        )

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No se proporcionaron datos para actualizar"
        )

    set_clause = ", ".join(
        f"{key} = :{key}" for key in update_data.keys()
    )

    result = await db.execute(
        sa.text(f"""
            UPDATE usuarios
            SET {set_clause}
            WHERE id = :user_id
            RETURNING id, nombre, email, is_active
        """),
        {"user_id": current_user["id"], **update_data}
    )
    updated_user = result.mappings().first()
    await db.commit()

    if not updated_user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return {
        "id": updated_user["id"],
        "nombre": updated_user["nombre"],
        "email": updated_user["email"],
        "activo": updated_user["is_active"]
    }


# ==============================================================
# ALIAS USUARIO ACTUAL
# ==============================================================

@router.get("/current_user", response_model=UsuarioResponse)
async def read_current_user_alias(
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    return {
        "id": current_user["id"],
        "nombre": current_user["nombre"],
        "email": current_user["email"],
        "activo": current_user["activo"]
    }
