from fastapi import WebSocket, status
from typing import Optional, Tuple
import jwt
from datetime import datetime, timedelta
import logging
from ....core.config import settings
from ...presentation.websocket.error_messages import ErrorMessageManager, ErrorType
from ..database.postgres_manager import postgres_manager

logger = logging.getLogger(__name__)

class WebSocketAuthenticator:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
    
    async def authenticate_websocket(self, websocket: WebSocket, token: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """Authenticate WebSocket with JWT and PostgreSQL session validation"""
        if not token:
            await self._close_with_error(websocket, ErrorType.AUTHENTICATION_FAILED, "Token required")
            return False, None
        
        try:
            # Verify JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            
            # Check if session is valid in PostgreSQL
            async with postgres_manager.get_connection() as conn:
                session = await conn.fetchrow('''
                    SELECT session_id, expires_at, is_active 
                    FROM user_sessions 
                    WHERE user_id = $1 AND is_active = TRUE AND expires_at > NOW()
                    ORDER BY last_activity DESC LIMIT 1
                ''', user_id)
                
                if not session:
                    await self._close_with_error(websocket, ErrorType.SESSION_EXPIRED, "Session expired")
                    return False, None
            
            return True, payload
            
        except jwt.ExpiredSignatureError:
            await self._close_with_error(websocket, ErrorType.SESSION_EXPIRED, "Token expired")
            return False, None
        except jwt.InvalidTokenError:
            await self._close_with_error(websocket, ErrorType.AUTHENTICATION_FAILED, "Invalid token")
            return False, None
        except Exception as e:
            await self._close_with_error(websocket, ErrorType.INTERNAL_ERROR, str(e))
            return False, None
    
    async def create_user_session(self, user_id: str, username: str, email: str, role: str, 
                                ip_address: str, user_agent: str) -> str:
        """Create new user session in PostgreSQL"""
        session_id = f"session_{user_id}_{datetime.now().timestamp()}"
        expires_at = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        async with postgres_manager.get_connection() as conn:
            await conn.execute('''
                INSERT INTO user_sessions 
                (session_id, user_id, username, email, role, login_time, last_activity, 
                 ip_address, user_agent, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (session_id) 
                DO UPDATE SET 
                    last_activity = EXCLUDED.last_activity,
                    expires_at = EXCLUDED.expires_at,
                    is_active = TRUE
            ''', session_id, user_id, username, email, role, datetime.now(), 
               datetime.now(), ip_address, user_agent, expires_at)
        
        return session_id
    
    async def update_session_activity(self, user_id: str):
        """Update session last activity timestamp"""
        async with postgres_manager.get_connection() as conn:
            await conn.execute('''
                UPDATE user_sessions 
                SET last_activity = NOW() 
                WHERE user_id = $1 AND is_active = TRUE
            ''', user_id)
    
    async def _close_with_error(self, websocket: WebSocket, error_type: ErrorType, details: str = None):
        """Close connection with error message"""
        error_msg = ErrorMessageManager.get_error_message(error_type, details)
        try:
            await websocket.send_json({"error": error_msg, "status": "error"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        except:
            pass

websocket_auth = WebSocketAuthenticator()