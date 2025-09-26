# from api_key_service import APIKey
from ..models.api_key_models import APIKey
from ..schemas.api_keys_schemas import APIkeyCreate, APIkeyResponse, APIkeyInfo

api_key_manager = APIKey()


async def create_api_key(key_data: APIkeyCreate) -> APIkeyResponse:
    return await api_key_manager.create_key(
        user_id=key_data.user_id,
        permissions=key_data.permissions,
        expires_in_days= key_data.expires_in_days
    )
async def validate_api_key(key: str) -> APIkeyInfo:
    key_data = await api_key_manager.validate_key(key)
    if not key_data:
        return None
    return APIkeyInfo(**key_data)