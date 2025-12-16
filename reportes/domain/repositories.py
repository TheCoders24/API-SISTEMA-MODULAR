# reportes/domain/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .entities import Reporte, TipoReporte, EstadoReporte

class ReporteRepository(ABC):
    @abstractmethod
    async def obtener_por_id(self, reporte_id: str) -> Optional[Reporte]:
        pass
    
    @abstractmethod
    async def obtener_todos(
        self,
        skip: int = 0,
        limit: int = 10,
        tipo: Optional[TipoReporte] = None,
        estado: Optional[EstadoReporte] = None,
        usuario_id: Optional[str] = None
    ) -> List[Reporte]:
        pass
    
    @abstractmethod
    async def crear(self, reporte: Reporte) -> Reporte:
        pass
    
    @abstractmethod
    async def actualizar(self, reporte_id: str, updates: Dict[str, Any]) -> Optional[Reporte]:
        pass
    
    @abstractmethod
    async def eliminar(self, reporte_id: str) -> bool:
        pass
    
    @abstractmethod
    async def actualizar_estado(self, reporte_id: str, estado: EstadoReporte) -> bool:
        pass
    
    @abstractmethod
    async def incrementar_descargas(self, reporte_id: str) -> bool:
        pass
    
    @abstractmethod
    async def obtener_estadisticas(self) -> Dict[str, Any]:
        pass