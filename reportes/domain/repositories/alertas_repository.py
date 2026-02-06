from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..entities.Alertas import Alerta, EstadisticasAlertas, TipoAlerta, SeveridadAlerta
class AlertasRepository(ABC):
    @abstractmethod
    async def obtener_alertas_activas(self, severidad: Optional[SeveridadAlerta] = None,
                                     tipo: Optional[TipoAlerta] = None) -> List[Alerta]:
        pass
    
    @abstractmethod
    async def obtener_alerta_por_id(self, alerta_id: str) -> Optional[Alerta]:
        pass
    
    @abstractmethod
    async def crear_alerta(self, tipo: TipoAlerta, titulo: str, descripcion: str,
                          metrica_id: str, severidad: SeveridadAlerta,
                          accion_recomendada: Optional[str] = None) -> Alerta:
        pass
    
    @abstractmethod
    async def resolver_alerta(self, alerta_id: str) -> Alerta:
        pass
    
    @abstractmethod
    async def obtener_estadisticas(self) -> EstadisticasAlertas:
        pass
    
    @abstractmethod
    async def suscribir_notificaciones(self, callback):
        pass