from fastapi import FastAPI
from .productos.presentation.routes import router as productos_router
from .Login.routes import router as login_router
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from proveedores.routes import router as proveedores_router
from .database.base import Base
from .database.session import engine
from .Api_Keys_Session.services.api_key_service import create_api_key, validate_api_key
from .Api_Keys_Session.schemas.api_keys_schemas import APIkeyCreate, APIkeyResponse, APIkeyInfo
from fastapi.security import APIKeyHeader
from database.session import DATABASE_URL
from sqlalchemy.orm import Session

app = FastAPI()

# Incluye los routers de cada módulo
app.include_router(productos_router)
app.include_router(login_router)
# app.include_router(proveedores_router)

api_key_header = APIKeyHeader(name="X-API-Key")

async def get_current_user(api_key: str = Depends(api_key_header), db: Session = Depends(DATABASE_URL)):
    key_info = await validate_api_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o expirada"
        )
    
    # Aquí puedes verificar el usuario en PostgreSQL si es necesario
    # user = db.query(User).filter(User.id == key_info.user_id).first()
    
    return {"user_id": key_info.user_id, "permissions": key_info.permissions}

@app.post("/api-keys/", response_model= APIkeyInfo)
async def generate_new_key(key_data: APIkeyCreate):
    return await create_api_key(key_data)

@app.get("/protected-route/")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Acceso autorizado",
        "user_id": current_user["user_id"],
        "permissions": current_user["permissions"]
    }


@app.get("/")
async def root():
    return {"message": "Sistema de Inventario con PostgreSQL"}