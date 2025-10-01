from fastapi import FastAPI, Request
from fastapi import Depends, HTTPException, status
from .productos.presentation.routes import router as productos_router
from .Login.routes import router as login_router
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from .database.base import Base
from .database.session import engine
from .Api_Keys_Session.models.api_key_models import create_key, validate_key
from .Api_Keys_Session.schemas.api_keys_schemas import APIkeyCreate, APIkeyResponse, APIkeyInfo
from fastapi.security import APIKeyHeader
from .database.session import DATABASE_URL
from .database.session import get_db
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from .categoria.presentation.routes.categoria_router import categoria_router
from .proveedores.presentation.routes.proveedores_router import proveedores_router
from .Api_Keys_Session.services.api_key_service import create_api_key, validate_api_key
from .webSocket.presentation.websocket.routes import websocket
from .logger.presentation.websocket.routes import websocket_router
from .monitoring.monitoreodb.endpoint import router as monitoreo_router
from .monitoring.monitoreodb.manager import stats_background_task
import logging
from logging.config import dictConfig
import uvicorn
from .v2.message_routes import router_v2_
from .Ventas import router as ventas_router

# Configuración avanzada de logging
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(asctime)s [%(levelname)s] %(message)s",
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(asctime)s [%(levelname)s] %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}
# Aplicar configuración de logging
dictConfig(LOG_CONFIG)
# Crear logger personalizado
logger = logging.getLogger("api")
logger.setLevel(logging.INFO)
app = FastAPI(title="API Inventario v1")
app = FastAPI(title="API Inventario v2")

# Middleware para registrar todas las solicitudes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    # Registrar todas las solicitudes con su código de estado
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response

#incluimos la version de la api/v2 en pruebas
app.include_router(router_v2_ ,prefix="/api/v2")

# incluimos el router de monitoreo con su routers o prefijo
app.include_router(monitoreo_router, prefix="/monitoreo", tags=["monitoreo"])

# Incluye los routers de cada módulo
app.include_router(ventas_router)
app.include_router(websocket_router)
app.include_router(websocket)
app.include_router(productos_router)
app.include_router(login_router)
app.include_router(categoria_router)
app.include_router(proveedores_router)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.193.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Sistema de Inventario con PostgreSQL"}

# Si ejecutas este archivo directamente
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )