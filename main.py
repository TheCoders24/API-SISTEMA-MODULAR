import asyncio
import sys
import os
import logging
import traceback  # 👈 Importante para ver el error real
from pathlib import Path
from fastapi import FastAPI, Request # 👈 Añadido Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from logging.config import dictConfig

# =======================================================
# CONFIGURACIÓN DE PATH
# =======================================================
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["PYTHONPATH"] = str(ROOT_DIR)

# =======================================================
# IMPORTS LOCALES
# =======================================================
from .database.base import Base
from .Login.routes import router as login_router
from .categoria.presentation.routes.categoria_router import categoria_router
from .proveedores.presentation.routes.proveedores_router import proveedores_router
from .productos.presentation.routes import router as productos_router
from .Ventas import router as ventas_router
from .reportes.presentation.routes.routes_reportes_metricas import router as metricas_router

# =======================================================
# LOGGING (DEBUG CONFIG)
# =======================================================
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "formatter": "standard",
        }
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "DEBUG"},
        "uvicorn.error": {"level": "DEBUG"},
        "fastapi": {"handlers": ["default"], "level": "DEBUG"},
    },
}
dictConfig(LOG_CONFIG)
logger = logging.getLogger("uvicorn")

# =======================================================
# API KEYS
# =======================================================
try:
    from .Api_keys_Session.presentation.routes.api_keys_router import api_key_router
    print("✅ API Keys module imported successfully")
except Exception: # Cambiado a Exception para capturar todo
    print("⚠️ API Keys module error:")
    traceback.print_exc()
    api_key_router = None

# =======================================================
# OBSERVABILITY IMPORTS (CON DEBUG REAL)
# =======================================================
OBSERVABILITY_AVAILABLE = False

try:
    from observability_logs.infrastructure.mongodb.connection import mongodb_connection
    from observability_logs.infrastructure.mongodb.repository import MongoDBLogRepository
    from observability_logs.infrastructure.middleware import ObservabilityMiddleware
    from observability_logs.infrastructure.websocket import WebSocketPublisher
    from observability_logs.application.service import ObservabilityLogService
    from observability_logs.application.alerts import SecurityAlertService
    from observability_logs.presentation import logs_router, ws_router
    from observability_logs.config import ObservabilityConfig

    OBSERVABILITY_AVAILABLE = True
    print("✅ Observability module imported successfully")

except Exception: # 🛠️ Si falla el import, veremos POR QUÉ
    print("❌ ERROR CRÍTICO IMPORTANDO OBSERVABILIDAD:")
    traceback.print_exc()

# =======================================================
# APP
# =======================================================
app = FastAPI(
    title="API Inventario - Sistema Modular",
    version="2.0.0",
    debug=True 
)

# =======================================================
# MIDDLEWARE DE INSPECCIÓN (DEBUG EN TIEMPO REAL)
# =======================================================
@app.middleware("http")
async def inspect_requests(request: Request, call_next):
    logger.debug(f"🔥 Recibiendo: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"✅ Finalizado: {request.url.path} -> Status {response.status_code}")
    return response

# =======================================================
# OBSERVABILITY SETUP
# =======================================================
if OBSERVABILITY_AVAILABLE:
    try:
        config = ObservabilityConfig()
        mongodb_connection.initialize(config)
        log_repository = MongoDBLogRepository()
        log_service = ObservabilityLogService(log_repository)
        ws_publisher = WebSocketPublisher() if config.ws_enabled else None
        alert_service = SecurityAlertService(log_repository)

        app.add_middleware(
            ObservabilityMiddleware,
            log_service=log_service,
            ws_publisher=ws_publisher
        )

        @app.on_event("startup")
        async def start_alert_worker():
            if config.alerts_enabled:
                asyncio.create_task(alert_worker(alert_service, config.alert_check_interval))

        @app.on_event("shutdown")
        async def shutdown_mongo():
            mongodb_connection.close()

        app.include_router(logs_router, prefix="/observability/logs")
        app.include_router(ws_router, prefix="/observability/ws")
        print("✅ Observability initialized correctly")

    except Exception:
        OBSERVABILITY_AVAILABLE = False
        print("❌ ERROR CONFIGURANDO OBSERVABILIDAD:")
        traceback.print_exc()

# =======================================================
# CORS Y ROUTERS (Igual que los tenías)
# =======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login_router)
app.include_router(productos_router)
app.include_router(categoria_router)
app.include_router(proveedores_router)
app.include_router(ventas_router)
app.include_router(metricas_router, prefix="/api/metricas")
if api_key_router:
    app.include_router(api_key_router)

@app.on_event("startup")
async def debug_routes():
    for route in app.routes:
        logger.debug(f"Route: {route.path}")

@app.get("/")
async def root():
    return {
        "status": "operational",
        "observability": OBSERVABILITY_AVAILABLE,
        "mongodb": "connected" if (OBSERVABILITY_AVAILABLE and mongodb_connection.is_connected()) else "disconnected"
    }

async def alert_worker(alert_service, interval: int):
    while True:
        await asyncio.sleep(interval)
        try:
            alert_service.analyze_and_alert()
        except Exception as e:
            logger.error(f"❌ Alert worker error: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")