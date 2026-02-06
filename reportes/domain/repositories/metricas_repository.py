from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..entities.metricas import (
    Dashboard, MetricaResumen, MetricaDetalle, MetricasRealtime,
    DatoHistorico, Periodo
)

class MetricasRepository(ABC):
    @abstractmethod
    async def obtener_dashboard(self, periodo: Periodo, usuario_id: Optional[str] = None) -> Dashboard:
        pass
    
    @abstractmethod
    async def obtener_metricas_realtime(self) -> MetricasRealtime:
        pass
    
    @abstractmethod
    async def obtener_metricas_historicas(self, metrica_id: str, dias: int = 7) -> List[DatoHistorico]:
        pass
    
    @abstractmethod
    async def crear_kpi_config(self, nombre: str, metrica_id: str, objetivo: float, unidad: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def guardar_metrica_historica(self, metrica_id: str, valor: float, 
                                       cambio: float = 0.0, meta: Optional[float] = None):
        pass