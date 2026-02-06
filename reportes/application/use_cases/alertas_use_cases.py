from typing import List, Dict, Any, Optional
from datetime import datetime
from ...domain.entities.Alertas import Alerta, EstadisticasAlertas, TipoAlerta, SeveridadAlerta
from ...domain.repositories.alertas_repository import AlertasRepository

class ObtenerAlertasActivasUseCase:
    def __init__(self, alertas_repository: AlertasRepository):
        self.alertas_repository = alertas_repository
    
    async def execute(self, severidad: Optional[SeveridadAlerta] = None, 
                     tipo: Optional[TipoAlerta] = None) -> List[Alerta]:
        """Obtener alertas activas con filtros opcionales"""
        return await self.alertas_repository.obtener_alertas_activas(severidad, tipo)

class CrearAlertaUseCase:
    def __init__(self, alertas_repository: AlertasRepository):
        self.alertas_repository = alertas_repository
    
    async def execute(self, tipo: TipoAlerta, titulo: str, descripcion: str,
                     metrica_id: str, severidad: SeveridadAlerta,
                     accion_recomendada: Optional[str] = None) -> Alerta:
        """Crear una nueva alerta"""
        return await self.alertas_repository.crear_alerta(
            tipo, titulo, descripcion, metrica_id, severidad, accion_recomendada
        )

class ResolverAlertaUseCase:
    def __init__(self, alertas_repository: AlertasRepository):
        self.alertas_repository = alertas_repository
    
    async def execute(self, alerta_id: str) -> Alerta:
        """Marcar una alerta como resuelta"""
        return await self.alertas_repository.resolver_alerta(alerta_id)

class ObtenerEstadisticasAlertasUseCase:
    def __init__(self, alertas_repository: AlertasRepository):
        self.alertas_repository = alertas_repository
    
    async def execute(self) -> EstadisticasAlertas:
        """Obtener estadísticas de alertas"""
        return await self.alertas_repository.obtener_estadisticas()