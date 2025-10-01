from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

@dataclass
class DetalleVenta:
    id: Optional[int]
    producto_id: int
    producto_nombre: str
    cantidad: int
    precio: Decimal
    subtotal: Decimal
    
    def __post_init__(self):
        self.subtotal = self.precio * self.cantidad

@dataclass
class Venta:
    id: Optional[int]
    fecha: datetime
    total: Decimal
    usuario_id: Optional[int]
    usuario_nombre: Optional[str]
    detalles: List[DetalleVenta]
    
    def __post_init__(self):
        if not self.detalles:
            self.detalles = []
        # Recalcular total basado en detalles
        if not self.total and self.detalles:
            self.total = sum(detalle.subtotal for detalle in self.detalles)

@dataclass
class ProductoVenta:
    id: int
    nombre: str
    precio: Decimal
    stock: int

@dataclass
class EstadisticasVentas:
    total_ventas: int
    ingresos_totales: Decimal
    promedio_venta: Decimal
    total_productos_vendidos: int
    ventas_hoy: int
    ingresos_hoy: Decimal