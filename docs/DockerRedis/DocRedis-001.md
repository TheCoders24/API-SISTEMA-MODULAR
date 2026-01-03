
Entiendo perfectamente. No necesitas complicarte con un `docker-compose.yml` completo si ya tienes Postgres y Mongo corriendo nativamente. Podemos levantar **únicamente Redis** con un solo comando de Docker y conectarlo a tu código actual.

Aquí tienes los pasos para integrar Redis por separado:

### 1. Levantar Redis en Docker (Consola)

Ejecuta este comando en tu terminal para descargar e iniciar el contenedor de Redis. Este comando mapea el puerto 6379 de Redis al mismo puerto en tu Windows/Localhost:

```bash
docker run --name redis-inventario -p 6379:6379 -d redis:7-alpine

```

> **Tip:** Para verificar que está corriendo, puedes escribir `docker ps`. Deberías ver el contenedor `redis-inventario` en la lista.

---

### 2. Configurar el Cliente en Python

Primero, asegúrate de tener instalada la librería necesaria en tu entorno virtual:

```bash
pip install redis

```

Luego, crea el archivo `database/Redis_Connection.py` (siguiendo tu estilo de nombres modulares):

```python
import redis.asyncio as redis
import os
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis: redis.Redis = None

    async def connect(self):
        """Inicializa la conexión a Redis."""
        try:
            self.redis = redis.from_url(self.url, decode_responses=True)
            # Prueba de conexión (ping)
            await self.redis.ping()
            logger.info("🚀 Conexión a Redis establecida exitosamente")
        except Exception as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            raise

    async def close(self):
        """Cierra la conexión."""
        if self.redis:
            await self.redis.close()
            logger.info("🔌 Conexión a Redis cerrada")

# Singleton para usar en toda la app
redis_manager = RedisManager()

```

---

### 3. Implementar la Lógica de "Preguntar al Cache"

Ahora, integra la lógica en tu servicio de productos. El flujo que pediste (preguntar al cache -> si no está, ir a Postgres -> guardar en cache) se ve así:

```python
import json
from database.Redis_Connection import redis_manager
from database.UnitofWork import UnitOfWork
from models.producto import Producto
from sqlalchemy import select

async def get_producto_smart(producto_id: int):
    cache_key = f"prod:{producto_id}"
    
    # 1. Preguntar a la Cache (Redis)
    cached_prod = await redis_manager.redis.get(cache_key)
    
    if cached_prod:
        print("⚡ [CACHE HIT] Cargado desde Redis")
        return json.loads(cached_prod)

    # 2. Si no está en cache, preguntar a Postgres
    print("🐘 [CACHE MISS] Consultando PostgreSQL...")
    async with UnitOfWork() as uow:
        result = await uow.session.execute(
            select(Producto).filter(Producto.id == producto_id)
        )
        producto = result.scalar_one_or_none()

        if producto:
            # Convertimos el objeto SQLAlchemy a un dict simple
            prod_dict = {
                "id": producto.id,
                "nombre": producto.nombre,
                "stock": producto.stock
            }
            
            # 3. Guardar en Cache por 10 minutos (600 seg) para la próxima vez
            await redis_manager.redis.setex(cache_key, 600, json.dumps(prod_dict))
            return prod_dict
            
    return None

```

---

### 4. Inicializar en `main.py`

Para que `redis_manager.redis` no sea `None`, debes conectar al iniciar FastAPI:

```python
# main.py
from database.Redis_Connection import redis_manager

@app.on_event("startup")
async def startup():
    await redis_manager.connect()
    # await mongo_manager.connect() # Tus otras conexiones...

@app.on_event("shutdown")
async def shutdown():
    await redis_manager.close()

```

---

### ¿Cómo probarlo?

1. **Primera carga:** Llama a la ruta en tu navegador. En la consola verás `Consultando PostgreSQL...`. Notarás un pequeño retraso.
2. **Actualizar (F5):** Llama de nuevo. En la consola verás `Cargado desde Redis`. La respuesta será instantánea (menos de 2ms).
3. **Cambio de datos:** Si actualizas el stock de un producto, recuerda ejecutar `await redis_manager.redis.delete(f"prod:{id}")` para que la cache no muestre datos viejos.

**¿Te gustaría que te ayude a crear una ruta tipo "Panel de Control" en FastAPI para ver cuántas llaves tienes guardadas en Redis actualmente?**