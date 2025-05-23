from fastapi import FastAPI
from .productos.routes import router as productos_router
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from proveedores.routes import router as proveedores_router
from .database.base import Base
from .database.session import engine

app = FastAPI()

# Incluye los routers de cada módulo
app.include_router(productos_router)
# app.include_router(proveedores_router)

@app.get("/")
async def root():
    return {"message": "Sistema de Inventario con PostgreSQL"}