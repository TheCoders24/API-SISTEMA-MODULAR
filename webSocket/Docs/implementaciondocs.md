 **actualizaciones en tiempo real con FastAPI, Postgres (LISTEN/NOTIFY) y WebSockets** para métricas y reportes.

---

# **Módulo `notifiws` – Actualizaciones en Tiempo Real**

Este módulo proporciona una infraestructura de **notificaciones en tiempo real** para el sistema de inventario, utilizando:

1. **Triggers de Postgres** para emitir eventos cuando se modifican los datos.
2. **Canales `LISTEN/NOTIFY`** para enviar mensajes asincrónicos.
3. **FastAPI + WebSockets** para transmitir eventos a todos los clientes conectados.
4. **Frontend React/Next.js** que reacciona a los eventos y actualiza gráficos, tablas y reportes en tiempo real.

---

## **Arquitectura General**

```
Postgres (Trigger NOTIFY)  --->  FastAPI (asyncpg Listener)
                                   |
                                   v
                           WebSockets Broadcast
                                   |
                                   v
                      Frontend (Next.js con eventos en vivo)
```

* **Base de datos:** Cada vez que ocurre un cambio (insertar venta, modificar stock, etc.), un **trigger** ejecuta la función `pg_notify`, enviando un mensaje JSON con la información del evento.
* **Backend:** Un proceso asíncrono de `asyncpg` escucha los canales de Postgres. Cuando llega un mensaje, lo retransmite a través de **WebSockets**.
* **Frontend:** Las aplicaciones cliente conectadas reciben automáticamente la notificación y actualizan sus componentes de UI (reportes, métricas, dashboards).

---

## **Componentes Clave**

### **1. Trigger en Postgres**

Ejemplo para la tabla `ventas`:

```sql
CREATE OR REPLACE FUNCTION notify_new_sale() RETURNS trigger AS $$
BEGIN
  PERFORM pg_notify('sales_channel', row_to_json(NEW)::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sales_trigger
AFTER INSERT ON ventas
FOR EACH ROW
EXECUTE FUNCTION notify_new_sale();
```

* Cada vez que se inserta una nueva venta, se envía un evento en el canal `sales_channel`.

---

### **2. Listener en FastAPI (asyncpg)**

```python
# notifiws/listener.py
import asyncpg
import asyncio
from .manager import ws_manager

async def handle_sales_notification(conn, pid, channel, payload):
    # Transmitir el evento a todos los clientes conectados
    await ws_manager.broadcast(payload)

async def start_sales_listener():
    conn = await asyncpg.connect(dsn="postgresql://user:password@localhost:5432/mi_db")
    await conn.add_listener("sales_channel", handle_sales_notification)
    print("Listening sales_channel...")
    while True:
        await asyncio.sleep(60)
```

* `start_sales_listener()` mantiene la conexión con Postgres y escucha el canal `sales_channel`.

---

### **3. WebSocket para el Frontend**

```python
# notifiws/routes.py
from fastapi import APIRouter, WebSocket
from .manager import ws_manager

router = APIRouter()

@router.websocket("/ws/sales")
async def websocket_sales(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        ws_manager.disconnect(ws)
```

* Cada cliente que se conecta al endpoint `/ws/sales` recibe actualizaciones automáticas.

---

### **4. Frontend React/Next.js**

```tsx
useEffect(() => {
  const ws = new WebSocket("ws://localhost:8000/ws/sales");
  
  ws.onmessage = (event) => {
    const newSale = JSON.parse(event.data);
    console.log("Nueva venta recibida:", newSale);
    // Aquí actualizas gráficos o métricas en tiempo real
  };

  return () => ws.close();
}, []);
```

* El frontend se conecta al WebSocket y actualiza la UI cuando llega una notificación.

---

## **Beneficios**

* **Actualizaciones instantáneas**: No necesitas recargar la página ni hacer polling.
* **Menos carga en el servidor**: Evita consultas repetitivas.
* **Experiencia de usuario mejorada**: Ideal para paneles de métricas, reportes y dashboards interactivos.

---

## **Casos de Uso en el Proyecto**

* **Métricas en tiempo real**: Mostrar un contador de ventas o ingresos que se actualiza automáticamente.
* **Notificaciones de inventario**: Avisar cuando un producto baja de stock sin recargar la página.
* **Reportes en vivo**: Tablas de ventas o actividades que se refrescan al instante.

---
