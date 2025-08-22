# presentation/websocket/error_messages.py
from typing import Dict, Any
from enum import Enum

class ErrorType(Enum):
    AUTHENTICATION_FAILED = "authentication_failed"
    INVALID_JSON = "invalid_json"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"
    UNAUTHORIZED = "unauthorized"
    SESSION_EXPIRED = "session_expired"
    CHANNEL_NOT_FOUND = "channel_not_found"
    USER_NOT_FOUND = "user_not_found"
    PERMISSION_DENIED = "permission_denied"

class ErrorMessageManager:
    _messages = {
        ErrorType.AUTHENTICATION_FAILED: {
            "code": "AUTH001",
            "message": "Autenticación fallida. Token inválido o expirado.",
            "severity": "high"
        },
        ErrorType.INVALID_JSON: {
            "code": "FORMAT001",
            "message": "Formato JSON inválido en el mensaje recibido.",
            "severity": "medium"
        },
        ErrorType.VALIDATION_ERROR: {
            "code": "VALID001",
            "message": "Error de validación en los datos recibidos.",
            "severity": "medium"
        },
        ErrorType.INTERNAL_ERROR: {
            "code": "SYS001",
            "message": "Error interno del servidor. Por favor, intente más tarde.",
            "severity": "critical"
        },
        ErrorType.UNAUTHORIZED: {
            "code": "AUTH002",
            "message": "No autorizado para realizar esta acción.",
            "severity": "high"
        },
        ErrorType.SESSION_EXPIRED: {
            "code": "AUTH003",
            "message": "Sesión expirada. Por favor, inicie sesión nuevamente.",
            "severity": "medium"
        },
        ErrorType.CHANNEL_NOT_FOUND: {
            "code": "CHAN001",
            "message": "Canal no encontrado.",
            "severity": "low"
        },
        ErrorType.USER_NOT_FOUND: {
            "code": "USER001",
            "message": "Usuario no encontrado.",
            "severity": "medium"
        },
        ErrorType.PERMISSION_DENIED: {
            "code": "PERM001",
            "message": "Permisos insuficientes para esta operación.",
            "severity": "high"
        }
    }
    
    @classmethod
    def get_error_message(cls, error_type: ErrorType, additional_info: str = None) -> Dict[str, Any]:
        """Obtiene mensaje de error predefinido con información adicional opcional"""
        message = cls._messages[error_type].copy()
        if additional_info:
            message["details"] = additional_info
        return message