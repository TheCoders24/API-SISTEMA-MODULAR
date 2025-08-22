# infrastructure/auth/websocket_auth.py
from fastapi import WebSocket, WebSocketDisconnect, status
from typing import Optional, Tuple
import jwt
from datetime import datetime
from ....core.config import settings
from ...presentation.websocket.error_messages import ErrorMessageManager, ErrorType

class WebSocketAuthenticator:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
    
    async def authenticate_websocket(self, websocket: WebSocket, token: Optional[str] = None) -> Tuple[bool, Optional[dict]]:
        """
        Autentica un WebSocket usando JWT token
        Returns: (is_authenticated, payload)
        """
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False, None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return True, payload
        except jwt.ExpiredSignatureError:
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.SESSION_EXPIRED, 
                "El token ha expirado"
            )
            await websocket.send_json({"error": error_msg, "status": "error"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False, None
        except jwt.InvalidTokenError:
            error_msg = ErrorMessageManager.get_error_message(
                ErrorType.AUTHENTICATION_FAILED,
                "Token inválido"
            )
            await websocket.send_json({"error": error_msg, "status": "error"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False, None

websocket_auth = WebSocketAuthenticator()