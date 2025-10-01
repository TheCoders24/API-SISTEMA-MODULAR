from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

class DetalleVentaDTO(BaseModel):
    producto_id: int
    cantidad: int

class CrearVentaDTO(BaseModel):
    detalles: List[DetalleVentaDTO]
    usuario_id: Optional[int] = None

class VentaResponseDTO(BaseModel):
    id: int
    fecha: datetime
    total: Decimal
    usuario_id: Optional[int]
    usuario_nombre: Optional[str]
    detalles: List[dict]

class EstadisticasResponseDTO(BaseModel):
    total_ventas: int
    ingresos_totales: Decimal
    promedio_venta: Decimal
    total_productos_vendidos: int
    ventas_hoy: int
    ingresos_hoy: Decimal