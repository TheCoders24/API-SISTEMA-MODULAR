from fastapi import FastAPI
from fastapi import Depends, HTTPException, status
from .productos.presentation.routes import router as productos_router
from .Login.routes import router as login_router
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from proveedores.routes import router as proveedores_router
from .database.base import Base
from .database.session import engine
#from Api_Keys_Session.models.api_key_models import create_api_key, validate_api_key
from .Api_Keys_Session.models.api_key_models import create_key, validate_key
from .Api_Keys_Session.schemas.api_keys_schemas import APIkeyCreate, APIkeyResponse, APIkeyInfo
from fastapi.security import APIKeyHeader
#from .database.session import DATABASE_URL
from .database.session import DATABASE_URL
from .database.session import get_db
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
# importamos la parte o el endpoint de categoria routers
from .categoria.presentation.routes.categoria_router import categoria_router
from .proveedores.presentation.routes.proveedores_router import proveedores_router
from .Api_Keys_Session.services.api_key_service import create_api_key, validate_api_key

app = FastAPI()

# Incluye los routers de cada módulo
app.include_router(productos_router)
app.include_router(login_router)
app.include_router(categoria_router)
app.include_router(proveedores_router)


# app.include_router(proveedores_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Cambia por el puerto donde corre tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Sistema de Inventario con PostgreSQL"}