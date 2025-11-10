from fastapi import APIRouter, Depends, HTTPException, Header, Path, Query, status
from typing import List

#from domain.repositories.api_key_repository import APIKeyRepository
#from infrastructure.databases.mongodb.api_key_repository import MongoDBAPIKeyRepository
#from application.services.api_key_service import APIKeyService
#from ..schemas.api_key_schemas import APIKeyCreate, APIKeyResponse, APIKeyInfo
from domain.entities.repositories.api_keys_repository import APIKeyRepository
from ...infrastructure.database.mongodb.api_keys_repository import MongoDBAPIKeyRepository
from ...application.service.api_keys_service import APIKeyService
from ..schemas.api_keys_schemas import APIKeyCreate, APIKeyResponse, APIKeyInfo



# Dependencia de inyección
def get_api_key_repository() -> APIKeyRepository:
    return MongoDBAPIKeyRepository()

def get_api_key_service(repo: APIKeyRepository = Depends(get_api_key_repository)) -> APIKeyService:
    return APIKeyService(repo)

api_key_router = APIRouter(prefix="/api-keys", tags=["API Keys"])

@api_key_router.post("/", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    service: APIKeyService = Depends(get_api_key_service)
):
    return await service.create_key(
        user_id=data.user_id,
        permissions=data.permissions,
        expires_in_days=data.expires_in_days,
        name=data.name,
        description=data.description
    )

@api_key_router.get("/validate", response_model=APIKeyInfo)
async def validate_api_key(
    x_api_key: str = Header(..., alias="X-API-KEY"),
    service: APIKeyService = Depends(get_api_key_service)
):
    key_info = await service.validate_key(x_api_key)
    if not key_info:
        raise HTTPException(status_code=403, detail="Invalid or expired API key")
    return key_info

@api_key_router.get("/user/{user_id}", response_model=List[APIKeyInfo])
async def get_user_keys(
    user_id: str = Path(...),
    service: APIKeyService = Depends(get_api_key_service)
):
    return await service.get_user_keys(user_id)

@api_key_router.post("/cleanup")
async def force_cleanup(service: APIKeyService = Depends(get_api_key_service)):
    deleted = await service.force_cleanup()
    return {"deleted_count": deleted}

@api_key_router.get("/stats")
async def get_stats(service: APIKeyService = Depends(get_api_key_service)):
    return await service.get_stats()