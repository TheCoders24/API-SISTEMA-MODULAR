from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import json
from ..infrastructure.websocket.manager import WebSocketManager
from ..presentation.websocket.schemas import NotificationSchema, UserRole
from ..presentation.websocket.error_messages import ErrorMessageManager, ErrorType
from ..infrastructure.database.postgres_manager import postgres_manager
from ..infrastructure.security.websocket_auth import websocket_auth
from ..infrastructure.websocket import manager

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, websocket_manager: WebSocketManager):
        self.ws_manager = websocket_manager
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user with PostgreSQL delivery tracking"""
        try:
            message_id = f"msg_{datetime.now().timestamp()}_{user_id}"
            message_with_id = {
                **message,
                "message_id": message_id,
                "delivery_status": "sent",
                "timestamp": datetime.now().isoformat()
            }
            
            # Store message in PostgreSQL before sending
            async with postgres_manager.get_connection() as conn:
                await conn.execute('''
                    INSERT INTO message_queue 
                    (message_id, channel, user_id, message_type, payload, priority, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', message_id, f"user_{user_id}", user_id, 
                   message.get('type', 'notification'), 
                   json.dumps(message), 
                   message.get('priority', 0), 
                   'pending')
            
            # Send via WebSocket
            await self.ws_manager.send_to_user(user_id, message_with_id)
            
            logger.info(f"Message sent to user {user_id}: {message_id}")
            
        except Exception as e:
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.INTERNAL_ERROR,
                f"Error sending message to user: {str(e)}"
            )
            logger.error(f"Error sending to user {user_id}: {e}")
            
            # Update message status to failed
            try:
                async with postgres_manager.get_connection() as conn:
                    await conn.execute('''
                        UPDATE message_queue 
                        SET status = 'failed', retry_count = retry_count + 1
                        WHERE message_id = $1
                    ''', message_id)
            except Exception as db_error:
                logger.error(f"Error updating message status: {db_error}")
            
            raise
    
    async def send_to_admins(self, message: Dict[str, Any]):
        """Send message to all administrators with PostgreSQL tracking"""
        try:
            message_id = f"admin_msg_{datetime.now().timestamp()}"
            message_with_id = {
                **message,
                "message_id": message_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store message in PostgreSQL
            async with postgres_manager.get_connection() as conn:
                await conn.execute('''
                    INSERT INTO message_queue 
                    (message_id, channel, message_type, payload, priority, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', message_id, "admin_dashboard", 
                   message.get('type', 'admin_notification'), 
                   json.dumps(message), 
                   message.get('priority', 0), 
                   'pending')
            
            # Send via WebSocket
            await self.ws_manager.broadcast("admin_dashboard", message_with_id)
            
            logger.info("Message sent to administrators")
            
        except Exception as e:
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.INTERNAL_ERROR,
                f"Error sending message to admins: {str(e)}"
            )
            logger.error(f"Error sending to admins: {e}")
            raise
    
    async def send_system_alert(self, alert_data: NotificationSchema):
        """Send system alert to relevant users with PostgreSQL persistence"""
        message = {
            "type": "system_alert",
            "data": alert_data.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Store alert in PostgreSQL
        async with postgres_manager.get_connection() as conn:
            await conn.execute('''
                INSERT INTO message_queue 
                (message_id, channel, message_type, payload, priority, status, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', f"alert_{datetime.now().timestamp()}", "system_alerts",
               "system_alert", json.dumps(alert_data.dict()),
               alert_data.priority, 'pending', alert_data.expires_at)
        
        # Send to admins for critical alerts
        if alert_data.priority in ["high", "critical"]:
            await self.send_to_admins(message)
        
        # Send to affected users if applicable
        if alert_data.data and "affected_users" in alert_data.data:
            for user_id in alert_data.data["affected_users"]:
                await self.send_to_user(user_id, message)
    
    async def get_user_messages(self, user_id: str, limit: int = 50, offset: int = 0):
        """Retrieve user's message history from PostgreSQL"""
        try:
            async with postgres_manager.get_connection() as conn:
                messages = await conn.fetch('''
                    SELECT message_id, message_type, payload, status, created_at, delivered_at
                    FROM message_queue 
                    WHERE user_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT $2 OFFSET $3
                ''', user_id, limit, offset)
                
                return [dict(msg) for msg in messages]
                
        except Exception as e:
            logger.error(f"Error retrieving user messages: {e}")
            return []
    
    async def cleanup_old_sessions(self):
        """Clean up expired sessions from PostgreSQL"""
        try:
            async with postgres_manager.get_connection() as conn:
                result = await conn.execute('''
                    UPDATE user_sessions 
                    SET is_active = FALSE 
                    WHERE expires_at < NOW() AND is_active = TRUE
                ''')
                logger.info(f"Cleaned up {result.split()[1]} expired sessions")
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")

# Factory function for dependency injection
def get_notification_service():
    return NotificationService(manager)