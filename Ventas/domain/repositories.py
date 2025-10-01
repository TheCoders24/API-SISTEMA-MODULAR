from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from .entities import Venta, EstadisticasVentas, ProductoVenta

class VentaRepository(ABC):
    @abstractmethod
    def get_by_id(self, venta_id: int) -> Optional[Venta]:
        pass
    
    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Venta]:
        pass
    
    @abstractmethod
    def save(self, venta: Venta) -> Venta:
        pass
    
    @abstractmethod
    def delete(self, venta_id: int) -> bool:
        pass
    
    @abstractmethod
    def get_by_fecha_range(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Venta]:
        pass
    
    @abstractmethod
    def get_by_producto(self, producto_id: int) -> List[Venta]:
        pass
    
    @abstractmethod
    def get_estadisticas(self) -> EstadisticasVentas:
        pass

class ProductoRepository(ABC):
    @abstractmethod
    def get_by_id(self, producto_id: int) -> Optional[ProductoVenta]:
        pass
    
    @abstractmethod
    def update_stock(self, producto_id: int, cantidad: int) -> bool:
        pass