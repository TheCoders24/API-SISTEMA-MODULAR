# presentation/websocket/routes.py
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks, Request
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import json
import asyncio

# from Login.auth import get_current_user
from ....Login.auth import get_current_user

# Importar el logger desde la nueva carpeta
# from ...infrastructure.logger import api_logger
from ...infrastructure import api_logger
from ...infrastructure.models import LogLevel
from ....webSocket.infrastructure.websocket.manager import ws_manager
from ....webSocket.application.notification_service import NotificationService,get_notification_service
from ....webSocket.presentation.websocket.schemas import (BroadcastRequest, UserRole, NotificationSchema,SystemHealthStatus)
from ....webSocket.presentation.websocket.error_messages import ErrorMessageManager, ErrorType

websocket_router = APIRouter()
websocket = websocket_router

# Ejemplo de endpoint con logging
@websocket_router.post("/websocket/admin/broadcast")
async def admin_broadcast(
    request: Request,
    broadcast_data: BroadcastRequest,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Broadcast avanzado para administradores"""
    try:
        sent_count = 0
        broadcast_message = {
            "type": "admin_broadcast",
            "data": broadcast_data.message,
            "timestamp": datetime.now().isoformat(),
            "broadcast_id": str(uuid.uuid4())
        }
        
        # ... código del broadcast ...
        
        return {
            "status": "success",
            "message": f"Broadcast enviado a {sent_count} clientes",
            "broadcast_id": broadcast_message["broadcast_id"],
            "recipient_count": sent_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Loggear el error con contexto completo
        api_logger.log_error(
            error_type="BROADCAST_ERROR",
            error_message="Error en broadcast administrativo",
            exception=e,
            endpoint="POST /websocket/admin/broadcast",
            request_data={
                "message": broadcast_data.message,
                "target_channels": broadcast_data.target_channels,
                "target_roles": broadcast_data.target_roles
            } if broadcast_data else None,
            additional_context={
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        error_msg = ErrorMessageManager.get_error_message(
            ErrorType.INTERNAL_ERROR,
            str(e)
        )
        raise HTTPException(status_code=500, detail=error_msg)

# Endpoints administrativos para logs
@websocket_router.get("/websocket/admin/logs")
async def get_error_logs(
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(get_current_user)
):
    """Obtener logs de errores"""
    try:
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        logs = api_logger.get_recent_errors(hours)
        
        return {
            "logs": logs,
            "hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        api_logger.log_error(
            error_type="LOGS_ACCESS_ERROR",
            error_message="Error accediendo a logs",
            exception=e,
            endpoint="GET /websocket/admin/logs"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@websocket_router.get("/websocket/admin/logs/files")
async def get_log_files(current_user: dict = Depends(get_current_user)):
    """Obtener lista de archivos de log disponibles"""
    try:
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        files = api_logger.get_log_files()
        
        return {
            "files": files,
            "total": len(files),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        api_logger.log_error(
            error_type="LOG_FILES_ERROR",
            error_message="Error listando archivos de log",
            exception=e,
            endpoint="GET /websocket/admin/logs/files"
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")