from typing import Optional, Any
from ..domain.value_objects import generate_trace_id


class LogContext:
    """Contexto de logging para una request/operación"""
    
    def __init__(self, request=None, user=None):
        self.trace_id = generate_trace_id()
        self.user_id = None
        self.role = None
        self.ip = None
        self.endpoint = None
        
        if user:
            self.user_id = getattr(user, "id", None)
            self.role = getattr(user, "role", None)
        
        if request:
            self.ip = self._extract_ip(request)
            self.endpoint = str(request.url) if hasattr(request, "url") else None
    
    def _extract_ip(self, request) -> Optional[str]:
        """Extrae IP del request considerando proxies"""
        if hasattr(request, "headers"):
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            return request.client.host if hasattr(request, "client") else None
        return None