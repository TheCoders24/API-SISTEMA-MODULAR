from fastapi import APIRouter, Depends, HTTPException, Header, Path, Query, status
# from ...services.api_key_service import create_api_key, validate_api_key as service_validate_api_key
from ...application.service.api_keys_service import CreateAPIKeyUseCase, ValidateAPIKeyUseCase
from typing import Annotated, List, Optional
# from ...schemas.api_keys_schemas import APIkeyCreate, APIkeyResponse, APIkeyInfo
from ..schemas.api_keys_schemas import APIKeyCreate, APIKeyResponse, APIKeyInfo
from ...models.api_key_models import api_key_manager
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from Login.auth import get_current_user

# usamos apirouter para definir lo que es la ruta de las creacion y validacion de api_keys
api_key_router = APIRouter("/api_keys", tags=["Api Keys"])


# Helps Informacon
def _mogno_doc_info(doc: dict) -> APIKeyInfo:
    print(f"[DEBUG][_mogno_doc_info] Convirtiendo documento Mongo -> APIkeyInfo: {doc}")
    return APIKeyInfo(
        user_id=str(doc.get("user_id")),
        permissions=doc.get("permissions", ["default"]),
        created_at=doc.get("created_at"),
        expires_at=doc.get("expires_at"),
        is_active=doc.get("is_active", False),
    )


# Crear API Key
@api_key_router.post(
    "/create",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar una nueva API Key",
    description="Crea una API Key para el usuario indicado Devuelve la clave cruda sola una vez",
)
async def generate_api_key(data: APIKeyCreate, get_current_user=Depends(get_current_user)):
    print(f"[DEBUG][generate_api_key] Datos recibidos: {data}")
    print(f"[DEBUG][generate_api_key] Usuario autenticado: {get_current_user}")

    result = await CreateAPIKeyUseCase(data)
    print(f"[DEBUG][generate_api_key] Resultado generado: {result}")

    return result


# Validamos que la API Key o Endpoint este Correctamente
@api_key_router.get(
    "/validate",
    response_model=APIKeyInfo,
    summary=" Validar una API Key",
    description="Verificamos si la API Key enviada en el Header X-API-KEY es valida y no esta expirada",
)
async def validate_key_endpoint(x_api_key: str = Header(..., alias="X-API-KEY")):
    print(f"[DEBUG][validate_key] X-API-KEY recibido: {x_api_key}")

    key_info = await validate_key_endpoint(x_api_key)
    print(f"[DEBUG][validate_key] Resultado del servicio: {key_info}")

    if not key_info:
        print("[DEBUG][validate_key] API Key inválida o expirada")
        raise HTTPException(status_code=403, detail="Info no Valida o Expiracion de la API Key")

    return key_info


# Listamos las API Keys por usuario
@api_key_router.get(
    "/user/{user_id}",
    response_model=List[APIKeyInfo],
    summary="Listar API Key de un Usuario",
)
async def listar_key_buscar_by_user(
    user_id: str = Path(..., description="ID del usuario propietario de las claves"),
    include_inactive: bool = Query(False, description="Incluir Claves Desactivadas"),
    current_user=Depends(get_current_user),
):
    print(f"[DEBUG][listar_key_buscar_by_user] user_id={user_id}, include_inactive={include_inactive}")
    print(f"[DEBUG][listar_key_buscar_by_user] Usuario autenticado: {current_user}")

    filter_q = {"user_id": user_id}
    if not include_inactive:
        filter_q["is_active"] = True

    print(f"[DEBUG][listar_key_buscar_by_user] Filtro Mongo: {filter_q}")

    cursor = api_key_manager.collection.find(filter_q)
    print("[DEBUG][listar_key_buscar_by_user] Ejecutando consulta Mongo...")

    docs = [docs async for doc in cursor]  # ❗ mantiene tu lógica original aunque esté mal
    print(f"[DEBUG][listar_key_buscar_by_user] Documentos obtenidos: {docs}")

    return [_mogno_doc_info(d) for d in docs]


# Desactivar una API Key
@api_key_router.patch(
    "/{key_id}/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar una API KEY",
)
async def deactivate_key(
    key_id: str = Path(..., description="ID de la clave"),
    current_user=Depends(get_current_user),
):
    print(f"[DEBUG][deactivate_key] key_id recibido = {key_id}")
    from bson import ObjectId

    try:
        oid = ObjectId(key_id)
        print(f"[DEBUG][deactivate_key] ObjectId válido: {oid}")
    except Exception as e:
        print(f"[DEBUG][deactivate_key] ERROR: ObjectId inválido: {e}")
        raise HTTPException(status_code=400, detail="key_id invalido")

    result = await api_key_manager.collection.update_one(
        {"_id": oid}, {"$set": {"is_active": False}}
    )

    print(f"[DEBUG][deactivate_key] matched_count={result.matched_count}")

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="API Key no encontrada")


# Rotar API Key
@api_key_router.post(
    "/{key_id}/rotate",
    response_model=APIKeyResponse,
    summary="Rotar (revocar y crear nueva) API Key",
)
async def rotate_key(
    key_id: str = Path(..., description="ID de la clave a rotar"),
    expires_in_days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
):
    print(f"[DEBUG][rotate_key] key_id={key_id}, expires_in_days={expires_in_days}")

    from bson import ObjectId

    try:
        oid = ObjectId(key_id)
        print(f"[DEBUG][rotate_key] ObjectId válido: {oid}")
    except Exception as e:
        print(f"[DEBUG][rotate_key] ERROR ObjectId inválido: {e}")
        raise HTTPException(status_code=400, detail="key_id inválido")

    doc = await api_key_manager.collection.find_one({"_id": oid})
    print(f"[DEBUG][rotate_key] Documento encontrado: {doc}")

    if not doc:
        print("[DEBUG][rotate_key] API Key no encontrada")
        raise HTTPException(status_code=404, detail="API Key no encontrada")

    print("[DEBUG][rotate_key] Desactivando API Key...")
    await api_key_manager.collection.update_one({"_id": oid}, {"$set": {"is_active": False}})

    # from ...schemas.api_keys_schemas import APIkeyCreate
    data = APIKeyCreate(
        user_id=str(doc["user_id"]),
        permissions=doc.get("permissions", ["default"]),
        expires_in_days=expires_in_days,
    )

    print(f"[DEBUG][rotate_key] Creando nueva API Key con data: {data}")

    new_key = await CreateAPIKeyUseCase(data)
    print(f"[DEBUG][rotate_key] Nueva API Key generada: {new_key}")

    return new_key


# Dependencia de seguridad
async def api_key_required(x_api_key: str = Header(..., alias="X-API-KEY")) -> APIKeyInfo:
    print(f"[DEBUG][api_key_required] X-API-KEY recibido: {x_api_key}")

    key_info = await ValidateAPIKeyUseCase(x_api_key)
    print(f"[DEBUG][api_key_required] Resultado de validación: {key_info}")

    if not key_info:
        print("[DEBUG][api_key_required] API Key inválida o expirada")
        raise HTTPException(status_code=403, detail="Invalid or expired API key")

    return key_info


# Endpoint protegido
@api_key_router.get(
    "/_test-protected",
    summary="Endpoint de prueba protegido por API Key",
    dependencies=[Depends(api_key_required)],
)
async def test_protected():
    print("[DEBUG][_test-protected] Acceso autorizado")
    return {"ok": True, "msg": "Acceso autorizado con API Key válida."}
