from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict, Optional
import time
from application.context import LogContext
from application.factory import LogFactory
from domain.enums import LogLevel, LogCategory
from domain.value_objects import generate_trace_id


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware global que inyecta trazabilidad en TODA la aplicación
    Versión CORREGIDA con tipos correctos
    """
    
    def __init__(
        self,
        app,
        log_service,
        ws_publisher=None,
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.log_service = log_service
        self.ws_publisher = ws_publisher
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/redoc"]
    
    async def dispatch(self, request: Request, call_next):
        # 1. Verificar exclusión
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)
        
        # 2. Obtener o generar trace_id
        trace_id = self._get_trace_id(request)
        
        # 3. Crear contexto
        context = LogContext(request=request)
        context.trace_id = trace_id
        
        # 4. Guardar en request.state
        request.state.log_context = context
        request.state.trace_id = trace_id
        
        # 5. Log de inicio
        start_time = time.time()
        
        start_log = LogFactory.create(
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            action="REQUEST_START",
            message=f"{request.method} {request.url.path}",
            context=context,
            metadata={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params)
            }
        )
        
        self.log_service.write(start_log)
        
        # 6. Publicar WebSocket
        if self.ws_publisher:
            await self.ws_publisher.publish(start_log)
        
        # 7. Ejecutar request
        try:
            response = await call_next(request)
            
            # 8. Log de fin
            duration = time.time() - start_time
            
            end_log = LogFactory.create(
                level=LogLevel.INFO,
                category=LogCategory.SYSTEM,
                action="REQUEST_END",
                message=f"Status: {response.status_code}",
                context=context,
                metadata={
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            self.log_service.write(end_log)
            
            # 9. Añadir header de trazabilidad
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            # 10. Log de error
            duration = time.time() - start_time
            
            error_log = LogFactory.create(
                level=LogLevel.ERROR,
                category=LogCategory.SYSTEM,
                action="REQUEST_ERROR",
                message=f"Error: {str(e)}",
                context=context,
                metadata={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            
            self.log_service.write(error_log)
            
            if self.ws_publisher:
                await self.ws_publisher.publish(error_log)
            
            raise
    
    def _get_trace_id(self, request: Request) -> str:
        """Obtiene trace_id de headers o genera uno nuevo"""
        trace_id = request.headers.get("X-Trace-ID")
        if not trace_id:
            trace_id = request.headers.get("X-Request-ID")
        if not trace_id:
            trace_id = generate_trace_id()
        return trace_id