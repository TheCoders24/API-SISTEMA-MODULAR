from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
import json
import logging
from datetime import datetime

# Importaciones relativas corregidas
from ...infrastructure.websocket.manager import WebSocketManager
from ...presentation.websocket.schemas import WSMessageSchema
from ...application.notification_service import NotificationService
from ...application.websocket_use_cases import WebSocketUseCases

# Logger correcto
logger = logging.getLogger(__name__)

websocket_router = APIRouter()
ws_manager = WebSocketManager()

# Dependencia
def get_notification_service():
    return NotificationService()

def get_websocket_use_cases(
    notification_service: NotificationService = Depends(get_notification_service)
):
    return WebSocketUseCases(notification_service)

@websocket_router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    """WebSocket endpoint de comunicacion en real-time"""
    
    await websocket.accept()
    await ws_manager.connect(websocket, channel)
    
    use_cases = get_websocket_use_cases()
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                validated_message = WSMessageSchema(**message_data)
                await use_cases.handle_event(validated_message, websocket, channel)
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON format",
                    "status": "error"
                })
            except ValidationError as e:
                await websocket.send_json({
                    "error": f"Validation error: {str(e)}",
                    "status": "error"
                })
            except Exception as e:
                await websocket.send_json({
                    "error": f"Internal server error: {str(e)}",
                    "status": "error"
                })
                logger.error(f"Error processing message: {e}")
                
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, channel)
        logger.info(f"Client disconnected from channel: {channel}")
    except Exception as e:
        logger.critical(f"WebSocket Error: {e}")
        await ws_manager.disconnect(websocket, channel)

# ✅ SOLUCIÓN: AÑADIR ESTA LÍNEA AL FINAL
websocket = websocket_router