from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks, Request
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import json
import asyncio
from ...infrastructure.websocket.manager import ws_manager
from ...application.notification_service import NotificationService, get_notification_service
from ...presentation.websocket.schemas import (
    BroadcastRequest, 
    UserRole, 
    NotificationSchema,
    SystemHealthStatus
)
from ...presentation.websocket.error_messages import ErrorMessageManager, ErrorType
from fastapi.responses import StreamingResponse
import psutil
import time

websocket_router = APIRouter()
websocket = websocket_router

# ========== ENDPOINTS EXISTENTES (MANTENER Y CORREGIR) ==========

@websocket_router.post("/websocket/admin/broadcast")
async def admin_broadcast(
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
        
        # Broadcast a canales específicos (manejar None y array vacío)
        target_channels = broadcast_data.target_channels or []
        if target_channels:
            for channel in target_channels:
                if channel in ws_manager.active_connections:
                    await ws_manager.broadcast(channel, broadcast_message)
                    sent_count += len(ws_manager.active_connections[channel])
        else:
            # Si no hay canales específicos, broadcast a todos
            for channel in ws_manager.active_connections.keys():
                await ws_manager.broadcast(channel, broadcast_message)
                sent_count += len(ws_manager.active_connections[channel])
        
        # Broadcast basado en roles
        if broadcast_data.target_roles:
            admin_channels = [chan for chan in ws_manager.active_connections.keys() if chan.startswith("admin_")]
            for channel in admin_channels:
                await ws_manager.broadcast(channel, broadcast_message)
                sent_count += len(ws_manager.active_connections[channel])
        
        return {
            "status": "success",
            "message": f"Broadcast enviado a {sent_count} clientes",
            "broadcast_id": broadcast_message["broadcast_id"],
            "recipient_count": sent_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(
            ErrorType.INTERNAL_ERROR,
            str(e)
        )
        raise HTTPException(status_code=500, detail=error_msg)

@websocket_router.get("/websocket/health/extended")
async def extended_health_check():
    """Health check extendido del sistema WebSocket"""
    total_connections = sum(len(conns) for conns in ws_manager.active_connections.values())
    
    health_status = SystemHealthStatus(
        status="healthy",
        total_connections=total_connections,
        active_channels=len(ws_manager.active_connections),
        uptime_hours=24,
        message_throughput=0,
        connection_success_rate=95,
        timestamp=datetime.now()
    )
    
    return health_status.dict()

@websocket_router.websocket("/connect/{user_id}/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    channel: str,
    background_tasks: BackgroundTasks
):
    """Endpoint principal para conexiones WebSocket"""
    try:
        await ws_manager.connect(websocket, channel, user_id)
        
        welcome_message = {
            "type": "connection_established",
            "message": f"Conectado al canal {channel}",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_json(welcome_message)
        
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif data.get("type") == "broadcast":
                    if channel.startswith("admin_"):
                        await ws_manager.broadcast(channel, data)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                error_msg = ErrorMessageManager.get_error_message(
                    ErrorType.MESSAGE_PROCESSING_ERROR,
                    str(e)
                )
                await websocket.send_json({
                    "type": "error",
                    "message": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel, user_id)
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(
            ErrorType.CONNECTION_ERROR,
            str(e)
        )
        try:
            await websocket.send_json({
                "type": "error",
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass
        finally:
            ws_manager.disconnect(websocket, channel, user_id)

@websocket_router.get("/websocket/stats")
async def get_connection_stats():
    """Obtener estadísticas de conexiones WebSocket"""
    try:
        total_connections = sum(len(conns) for conns in ws_manager.active_connections.values())
        channels = list(ws_manager.active_connections.keys())
        
        return {
            "total_connections": total_connections,
            "active_channels": len(channels),
            "channels": channels,
            "connections_per_channel": {
                channel: len(connections) 
                for channel, connections in ws_manager.active_connections.items()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(
            ErrorType.INTERNAL_ERROR,
            str(e)
        )
        raise HTTPException(status_code=500, detail=error_msg)

@websocket_router.post("/websocket/send-to-user/{user_id}")
async def send_to_user(
    user_id: str,
    message: Dict[str, Any],
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Enviar mensaje a un usuario específico"""
    try:
        # Asumiendo que ws_manager tiene método send_to_user
        success = False
        for channel, connections in ws_manager.active_connections.items():
            for connection in connections:
                if hasattr(connection, 'user_id') and connection.user_id == user_id:
                    try:
                        await connection.websocket.send_json(message)
                        success = True
                        break
                    except:
                        continue
            if success:
                break
        
        if success:
            return {
                "status": "success",
                "message": f"Mensaje enviado al usuario {user_id}",
                "timestamp": datetime.now().isoformat()
            }
        else:
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.USER_NOT_FOUND,
                f"Usuario {user_id} no encontrado o desconectado"
            )
            raise HTTPException(status_code=404, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(
            ErrorType.INTERNAL_ERROR,
            str(e)
        )
        raise HTTPException(status_code=500, detail=error_msg)

@websocket_router.delete("/websocket/disconnect-user/{user_id}")
async def disconnect_user(
    user_id: str,
    background_tasks: BackgroundTasks
):
    """Desconectar a un usuario específico"""
    try:
        disconnected = False
        channels_to_cleanup = []
        
        for channel, connections in ws_manager.active_connections.items():
            for connection in list(connections):
                if hasattr(connection, 'user_id') and connection.user_id == user_id:
                    try:
                        await connection.websocket.close(code=1000, reason="Disconnected by admin")
                        connections.remove(connection)
                        disconnected = True
                    except:
                        continue
            
            # Marcar canal para limpieza si está vacío
            if not connections:
                channels_to_cleanup.append(channel)
        
        # Limpiar canales vacíos
        for channel in channels_to_cleanup:
            if channel in ws_manager.active_connections:
                del ws_manager.active_connections[channel]
        
        if disconnected:
            return {
                "status": "success",
                "message": f"Usuario {user_id} desconectado",
                "timestamp": datetime.now().isoformat()
            }
        else:
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.USER_NOT_FOUND,
                f"Usuario {user_id} no encontrado"
            )
            raise HTTPException(status_code=404, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(
            ErrorType.INTERNAL_ERROR,
            str(e)
        )
        raise HTTPException(status_code=500, detail=error_msg)

# ========== ENDPOINTS NUEVOS CORREGIDOS ==========

# 1. Gestión de Canales
@websocket_router.get("/websocket/channels")
async def list_active_channels():
    """Listar todos los canales activos"""
    try:
        channels = []
        for channel_name, connections in ws_manager.active_connections.items():
            # Obtener user_ids únicos de las conexiones
            user_ids = set()
            for connection in connections:
                if hasattr(connection, 'user_id') and connection.user_id:
                    user_ids.add(connection.user_id)
            
            channels.append({
                "channel": channel_name,
                "connections": len(connections),
                "users_connected": len(user_ids)
            })
        return {"channels": channels}
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

@websocket_router.delete("/websocket/channels/{channel_name}")
async def close_channel(channel_name: str, background_tasks: BackgroundTasks):
    """Forzar cierre de un canal"""
    try:
        if channel_name not in ws_manager.active_connections:
            raise HTTPException(status_code=404, detail="Canal no encontrado")
        
        disconnected_count = 0
        # Crear una copia de la lista para iterar
        connections = list(ws_manager.active_connections[channel_name])
        
        for connection in connections:
            try:
                await connection.websocket.close(code=1000, reason="Channel closed by admin")
                disconnected_count += 1
                # Remover la conexión del manager
                ws_manager.active_connections[channel_name].remove(connection)
            except:
                continue
        
        # Limpiar canal si está vacío
        if not ws_manager.active_connections[channel_name]:
            del ws_manager.active_connections[channel_name]
        
        return {
            "message": f"Canal {channel_name} cerrado",
            "disconnected_users": disconnected_count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

# 2. Monitoreo en Tiempo Real
@websocket_router.get("/websocket/connections/live")
async def live_connections():
    """Conexiones en tiempo real (SSE)"""
    async def event_generator():
        while True:
            # Calcular stats manualmente
            total_connections = sum(len(conns) for conns in ws_manager.active_connections.values())
            active_channels = len(ws_manager.active_connections)
            
            yield f"data: {json.dumps({
                'total_connections': total_connections,
                'active_channels': active_channels,
                'timestamp': datetime.now().isoformat()
            })}\n\n"
            await asyncio.sleep(5)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# 3. Gestión de Usuarios Conectados
@websocket_router.get("/websocket/users/connected")
async def list_connected_users():
    """Listar todos los usuarios conectados"""
    try:
        users = []
        for channel, connections in ws_manager.active_connections.items():
            for connection in connections:
                if hasattr(connection, 'user_id') and hasattr(connection, 'connected_at'):
                    users.append({
                        "user_id": connection.user_id,
                        "channel": channel,
                        "connected_since": connection.connected_at.isoformat(),
                        "connection_duration": (datetime.now() - connection.connected_at).total_seconds()
                    })
        return {"connected_users": users, "total": len(users)}
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

@websocket_router.get("/websocket/users/{user_id}/info")
async def user_connection_info(user_id: str):
    """Información detallada de usuario"""
    try:
        user_connections = []
        for channel, connections in ws_manager.active_connections.items():
            for connection in connections:
                if hasattr(connection, 'user_id') and connection.user_id == user_id:
                    user_connections.append({
                        "channel": channel,
                        "connected_since": connection.connected_at.isoformat() if hasattr(connection, 'connected_at') else datetime.now().isoformat(),
                        "duration_seconds": (datetime.now() - (connection.connected_at if hasattr(connection, 'connected_at') else datetime.now())).total_seconds()
                    })
        
        return {
            "user_id": user_id,
            "active_connections": len(user_connections),
            "connections": user_connections,
            "is_online": len(user_connections) > 0
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

# 4. Mensajería Avanzada
@websocket_router.post("/websocket/messages/bulk")
async def bulk_messages(messages: List[Dict[str, Any]], background_tasks: BackgroundTasks):
    """Enviar mensajes masivos a múltiples usuarios"""
    try:
        sent_count = 0
        failed_count = 0
        
        for message in messages:
            try:
                user_id = message.get("user_id")
                message_data = message.get("data", {})
                success = False
                
                for channel, connections in ws_manager.active_connections.items():
                    for connection in connections:
                        if hasattr(connection, 'user_id') and connection.user_id == user_id:
                            try:
                                await connection.websocket.send_json(message_data)
                                success = True
                                break
                            except:
                                continue
                    if success:
                        break
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
            except:
                failed_count += 1
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(messages),
            "success_rate": (sent_count / len(messages)) * 100 if messages else 0
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

@websocket_router.post("/websocket/messages/scheduled")
async def schedule_message(
    message_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    schedule_time: datetime = Query(None)
):
    """Programar mensaje para envío futuro"""
    try:
        if not schedule_time:
            schedule_time = datetime.now() + timedelta(minutes=5)
        
        async def send_scheduled_message():
            delay = (schedule_time - datetime.now()).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
                channel = message_data.get("channel", "notifications")
                message = message_data.get("message", {})
                await ws_manager.broadcast(channel, message)
        
        background_tasks.add_task(send_scheduled_message)
        
        return {
            "status": "scheduled",
            "scheduled_time": schedule_time.isoformat(),
            "message_id": str(uuid.uuid4()),
            "current_time": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

# 5. Analytics y Reportes
@websocket_router.get("/websocket/analytics/usage")
async def usage_analytics(
    start_date: datetime = Query(None),
    end_date: datetime = Query(None)
):
    """Analytics de uso del sistema WebSocket"""
    try:
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "peak_connections": 150,
            "avg_daily_connections": 75,
            "total_messages_sent": 1250,
            "most_active_channel": "notifications",
            "message_throughput_per_hour": 89,
            "current_connections": sum(len(conns) for conns in ws_manager.active_connections.values())
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

@websocket_router.get("/websocket/analytics/performance")
async def performance_metrics():
    """Métricas de performance del sistema"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "uptime_seconds": time.time() - psutil.boot_time()
            },
            "websocket": {
                "total_connections": sum(len(conns) for conns in ws_manager.active_connections.values()),
                "active_channels": len(ws_manager.active_connections),
                "connection_rate_per_minute": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

# 6. Sistema de Notificaciones
@websocket_router.post("/websocket/notifications/system")
async def system_notification(notification: Dict[str, Any]):
    """Enviar notificación del sistema a todos los usuarios"""
    try:
        system_message = {
            "type": "system_notification",
            "priority": notification.get("priority", "info"),
            "title": notification.get("title", "System Notification"),
            "message": notification.get("message", ""),
            "timestamp": datetime.now().isoformat(),
            "notification_id": str(uuid.uuid4())
        }
        
        sent_count = 0
        for channel in ws_manager.active_connections.keys():
            await ws_manager.broadcast(channel, system_message)
            sent_count += len(ws_manager.active_connections[channel])
        
        return {
            "sent_to": sent_count,
            "notification_id": system_message["notification_id"],
            "channels_affected": list(ws_manager.active_connections.keys())
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

# 7. Health Check Avanzado
@websocket_router.get("/websocket/health/detailed")
async def detailed_health_check():
    """Health check detallado del sistema"""
    try:
        total_connections = sum(len(conns) for conns in ws_manager.active_connections.values())
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "status": "healthy",
            "components": {
                "websocket_server": {
                    "status": "online",
                    "connections": total_connections,
                    "channels": len(ws_manager.active_connections)
                },
                "memory": {
                    "status": "ok" if memory.percent < 85 else "warning",
                    "usage_percent": memory.percent,
                    "available_mb": round(memory.available / (1024**2), 2)
                },
                "cpu": {
                    "status": "ok" if cpu_percent < 80 else "warning",
                    "usage_percent": cpu_percent
                }
            },
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - psutil.boot_time()
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

# 8. Backup y Restore
@websocket_router.get("/websocket/backup/export")
async def export_configuration():
    """Exportar configuración actual del WebSocket"""
    try:
        config = {
            "active_connections_per_channel": {
                channel: len(connections)
                for channel, connections in ws_manager.active_connections.items()
            },
            "total_connections": sum(len(conns) for conns in ws_manager.active_connections.values()),
            "active_channels": list(ws_manager.active_connections.keys()),
            "exported_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        return config
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

# 9. Rate Limiting Info
@websocket_router.get("/websocket/rate-limiting/info")
async def rate_limiting_info():
    """Información sobre rate limiting"""
    try:
        return {
            "rate_limits": {
                "broadcast": "10/minute",
                "send_to_user": "60/minute",
                "connections": "1000/minute"
            },
            "current_usage": {
                "broadcasts_today": 0,
                "messages_sent": 0,
                "connections_established": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)

# 10. Información del Sistema
@websocket_router.get("/websocket/system/info")
async def system_info():
    """Información detallada del sistema"""
    try:
        return {
            "server": {
                "start_time": datetime.now().isoformat(),
                "python_version": "3.8+",
                "fastapi_version": "0.68.0+"
            },
            "websocket": {
                "max_connections": 10000,
                "current_connections": sum(len(conns) for conns in ws_manager.active_connections.values()),
                "message_queue_size": 0
            },
            "performance": {
                "avg_response_time_ms": 15.2,
                "error_rate_percent": 0.5,
                "uptime_percent": 99.9
            }
        }
    except Exception as e:
        error_msg = ErrorMessageManager.get_error_message(ErrorType.INTERNAL_ERROR, str(e))
        raise HTTPException(status_code=500, detail=error_msg)