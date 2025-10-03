from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ..application.services import LogService, is_suspicious

class LogSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.log_service = LogService()

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        route = str(request.url.path)
        body_bytes = await request.body()
        payload = body_bytes.decode(errors="ignore")

        # Bloqueo
        if await self.log_service.is_ip_blocked(ip):
            return JSONResponse({"detail":"Demasiados intentos sospechosos"}, status_code=429)

        response = await call_next(request)

        # Registrar si error 4xx o patrón sospechoso
        if response.status_code >= 400 or is_suspicious(payload):
            await self.log_service.register_attempt(ip, route, payload)

        return response
