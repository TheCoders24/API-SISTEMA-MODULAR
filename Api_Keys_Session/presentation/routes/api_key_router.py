'''
/Api_keys_Session/presentation/api_key_router.py
'''
from fastapi import APIRouter, Depends, HTTPException, Header,Path,Query,status
from ...services.api_key_service import create_api_key,validate_api_key as service_validate_api_key
from typing import Annotated, List, Optional
from ...schemas.api_keys_schemas import APIkeyCreate,APIkeyResponse,APIkeyInfo
from ...models.api_key_models import api_key_manager
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from Login.auth import get_current_user
# usamos apirouter para definir lo que es la ruta de las creacion y validacion de api_keys
api_key_router = APIRouter("/api_keys", tags=["Api Keys"])


# Helps Informacon
def _mogno_doc_info(doc: dict) -> APIkeyInfo:
    return APIkeyInfo(
        user_id=str(doc.get("user_id")),
        permissions=doc.get("permissions", ["default"]),
        created_at=doc.get("created_at"),
        expires_at=doc.get("expires_at"),
        is_active=doc.get("is_active", False),
    )

# Crear API Key
@api_key_router.post("/create", response_model=APIkeyResponse,
                status_code=status.HTTP_201_CREATED,
                summary= "Generar una nueva API Key",
                description= "Crea una API Key para el usuario indicado Devuelve la clave cruda sola una vez",
)
async def generate_api_key(data: APIkeyCreate, get_current_user = Depends(get_current_user)):
    """
    Genera una API Key

    si esta la auth Activa valida que la Data.user_id coincida con el current_user.id o que el usuario
    no se administrador

    """

    # Validamos que tengan los Permisos ejemplo el current_user_id, Current_user_administrador
    result = await create_api_key(data)
    return result # devolvemos lo que es la api key creada con la informacion correctamente


# Validamos que la API Key o Endpoint este Correctamente

@api_key_router.get("/validate", response_model=APIkeyInfo,
                    summary= " Validar una API Key",
                    description= "Verificamos si la API Key envidad en el Header X-API-KEY es valida y no esta expirada",   
                )
async def validate_key_endpoint(x_api_key: str = Header(..., alias="X-API-KEY")):
    key_info = await service_validate_api_key(x_api_key)
    if not key_info:
        raise HTTPException (status_code=403, detail="Info no Valida o Expiracion de la API Key")
    return key_info


# Listamos las API Keys por usuarios registrados o disponibles

@api_key_router.get("/user/{user_id}", 
                        response_model=List[APIkeyInfo],
                        summary= "Listar API Key de un Usuario",
                    )
async def listar_key_buscar_by_user(
    user_id: str =Path(..., description="ID del usuario propietario de las claves"),
    include_inactive: bool = Query(False, description="Incluir Claves Desactivadas"),
    current_user = Depends(get_current_user),
):
    #TODO: Validar Permisos el usuario debe ser admin
    filter_q = {"user_id": user_id}
    if not include_inactive:
        filter_q["is_active"] = True

    cursor = api_key_manager.collection.find(filter_q)
    docs = [docs async for doc in cursor]
    return [_mogno_doc_info(d) for d in docs]

# desactivamos lo que es la API Key usando el ID_USER
@api_key_router.patch("/{key_id}/deactivate",
                        status_code=status.HTTP_204_NO_CONTENT,
                        summary="Desactivar una API KEY",
                    )
async def deactivate_key(
    key_id: str = Path(..., description="ID de la clave"),
    current_user = Depends(get_current_user),
):
    #TODO valida permisos
    from bson import ObjectId

    try:
        oid = ObjectId(key_id)
    except Exception:
        raise HTTPException(status_code=400, detail="key_id invalido")
    
    result = await api_key_manager.collection.update_one(
        {"_id": oid}, {"$set":{"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="API Key no encontrada")
    

# Rotar (revocar + crear nueva) API Key

@api_key_router.post(
    "/{key_id}/rotate",
    response_model=APIkeyResponse,
    summary="Rotar (revocar y crear nueva) API Key",
)
async def rotate_key(
    key_id: str = Path(..., description="ID de la clave a rotar"),
    expires_in_days: int = Query(30, ge=1, le=365),
    current_user=Depends(get_current_user),
):
    """Marca la clave actual como inactiva y crea una nueva para el mismo usuario."""
    from bson import ObjectId

    try:
        oid = ObjectId(key_id)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="key_id inválido")

    doc = await api_key_manager.collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="API Key no encontrada")

    # TODO: valida permisos: current_user puede rotar solo sus claves o si es admin.

    # Desactiva actual
    await api_key_manager.collection.update_one({"_id": oid}, {"$set": {"is_active": False}})

    # Crea nueva
    from ...schemas.api_keys_schemas import APIkeyCreate
    data = APIkeyCreate(
        user_id=str(doc["user_id"]),
        permissions=doc.get("permissions", ["default"]),
        expires_in_days=expires_in_days,
    )
    new_key = await create_api_key(data)
    return new_key



# Dependencia reutilizable para proteger endpoints con API Key

async def api_key_required(x_api_key: str = Header(..., alias="X-API-KEY")) -> APIkeyInfo:
    """Dependencia para usar en cualquier endpoint protegido.

    Ejemplo:
        @router.get("/productos", dependencies=[Depends(api_key_required)])
        async def listar_productos(): ...
    """
    key_info = await service_validate_api_key(x_api_key)
    if not key_info:
        raise HTTPException(status_code=403, detail="Invalid or expired API key")
    return key_info



# Ejemplo de uso inline (puedes borrar si lo pondrás en otro router)

@api_key_router.get(
    "/_test-protected",
    summary="Endpoint de prueba protegido por API Key",
    dependencies=[Depends(api_key_required)],
)
async def test_protected():
    return {"ok": True, "msg": "Acceso autorizado con API Key válida."}

