from datetime import datetime
import logging
from typing import Dict, Any
import json
import asyncio
from ..presentation.websocket.schemas import WSMessageSchema, AuthMessageSchema
from ..presentation.websocket.error_messages import ErrorMessageManager, ErrorType
from ..infrastructure.websocket.manager import WebSocketManager
from ..infrastructure.security.websocket_auth import websocket_auth
from ..infrastructure.security.rate_limiter import rate_limiter
from ..infrastructure.database.postgres_manager import postgres_manager

logger = logging.getLogger(__name__)

class WebSocketUseCases:
    def __init__(self, notification_service):
        self.notification_service = notification_service
        self.ws_manager = WebSocketManager()
    
    async def handle_event(self, message: WSMessageSchema, websocket, channel: str):
        """Handle different WebSocket events with rate limiting"""
        # Rate limiting per connection
        connection_id = str(id(websocket))
        if await rate_limiter.is_rate_limited(f"conn_{connection_id}", 100, 60):
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.PERMISSION_DENIED,
                "Rate limit exceeded"
            )
            await websocket.send_json({"error": error_msg, "status": "error"})
            return
        
        try:
            if message.type == "auth":
                await self.handle_authentication(message.dict(), websocket, channel)
            elif message.type == "message":
                await self.handle_message(message.dict(), websocket, channel)
            elif message.type == "notification":
                await self.handle_notification(message.dict(), websocket, channel)
            elif message.type == "error_report":
                await self.handle_error_report(message.dict(), websocket, channel)
            else:
                await self.handle_unknown_event(message.dict(), websocket, channel)
                
        except Exception as e:
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.INTERNAL_ERROR,
                f"Error processing event: {str(e)}"
            )
            await websocket.send_json({
                "error": error_msg,
                "status": "error",
                "timestamp": datetime.now().isoformat()
            })
            logger.error(f"Error handling event: {e}")
    
    async def handle_authentication(self, auth_data: Dict[str, Any], websocket, channel: str):
        """Handle WebSocket authentication with PostgreSQL session management"""
        try:
            token = auth_data.get("token")
            is_authenticated, payload = await websocket_auth.authenticate_websocket(websocket, token)
            
            if is_authenticated:
                user_id = payload.get("sub")
                user_role = payload.get("role", "user")
                username = payload.get("username", "")
                email = payload.get("email", "")
                
                # Create or update user session in PostgreSQL
                session_id = await websocket_auth.create_user_session(
                    user_id, username, email, user_role,
                    auth_data.get("ip_address"), auth_data.get("user_agent")
                )
                
                # Determine final channel based on role
                final_channel = f"user_{user_id}" if user_role == "user" else "admin_dashboard"
                
                # Reconnect to appropriate channel
                await self.ws_manager.disconnect(websocket, "temp")
                await self.ws_manager.connect(websocket, final_channel, {
                    "user_id": user_id,
                    "role": user_role,
                    "session_id": session_id
                })
                
                success_msg = {
                    "type": "auth_success",
                    "message": "Authentication successful",
                    "user_id": user_id,
                    "role": user_role,
                    "channel": final_channel,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_json(success_msg)
                
                # Notify admins about new connection
                if user_role != "admin":
                    admin_notification = {
                        "type": "user_connected",
                        "user_id": user_id,
                        "role": user_role,
                        "timestamp": datetime.now().isoformat()
                    }
                    await self.notification_service.send_to_admins(admin_notification)
            else:
                error_msg = ErrorMessageManager.get_error_message(ErrorType.AUTHENTICATION_FAILED)
                await websocket.send_json({"error": error_msg, "status": "error"})
                
        except Exception as e:
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.INTERNAL_ERROR,
                f"Authentication error: {str(e)}"
            )
            await websocket.send_json({"error": error_msg, "status": "error"})
            logger.error(f"Authentication error: {e}")
    
    async def handle_error_report(self, error_data: Dict[str, Any], websocket, channel: str):
        """Handle error reports from clients with PostgreSQL storage"""
        try:
            # Log error to PostgreSQL
            async with postgres_manager.get_connection() as conn:
                await conn.execute('''
                    INSERT INTO connection_metrics 
                    (connection_id, channel, event_type, success, error_message)
                    VALUES ($1, $2, $3, $4, $5)
                ''', str(id(websocket)), channel, 'error_report', False, 
                   json.dumps(error_data))
            
            logger.warning(f"Error reported by client: {error_data}")
            
            # Send to administrators
            error_report = {
                "type": "client_error",
                "data": error_data,
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            }
            await self.notification_service.send_to_admins(error_report)
            
            # Confirm reception
            await websocket.send_json({
                "type": "error_report_received",
                "message": "Error reported successfully",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.INTERNAL_ERROR,
                f"Error processing report: {str(e)}"
            )
            await websocket.send_json({"error": error_msg, "status": "error"})

# Factory function for dependency injection
def get_websocket_use_cases(notification_service):
    return WebSocketUseCases(notification_service)