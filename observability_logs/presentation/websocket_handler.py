from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import asyncio
from datetime import datetime
# from infrastructure.websocket import WebSocketPublisher, SubscriptionType
from ..infrastructure.websocket import WebSocketPublisher, SubscriptionType


router = APIRouter(prefix="/ws", tags=["websocket"])
publisher = WebSocketPublisher()


@router.websocket("/logs")
async def logs_websocket(
    websocket: WebSocket,
    type: str = Query("all"),
    filter: Optional[str] = Query(None)
):
    """WebSocket para logs en tiempo real"""
    
    # Validar tipo de suscripción
    try:
        sub_type = SubscriptionType(type.lower())
    except ValueError:
        await websocket.close(code=1008, reason=f"Invalid subscription type: {type}")
        return
    
    try:
        await publisher.connect(websocket, sub_type, filter)
        
        while True:
            # Mantener conexión viva
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        publisher.disconnect(websocket)


@router.websocket("/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """Dashboard completo en tiempo real (solo admin)"""
    await websocket.accept()
    
    try:
        while True:
            # Stats simulados - conectar con repositorio real
            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "logs_per_second": 12.5,
                "active_alerts": 3,
                "top_ips": ["192.168.1.100", "10.0.0.23", "172.16.0.45"],
                "error_rate": 0.5,
                "categories": {
                    "auth": 45,
                    "security": 12,
                    "system": 78,
                    "api": 34
                }
            }
            
            await websocket.send_json(stats)
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        pass