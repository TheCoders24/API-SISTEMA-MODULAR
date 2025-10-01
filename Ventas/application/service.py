from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from ..domain.entities import Venta, DetalleVenta, ProductoVenta, EstadisticasVentas
from ..domain.repositories import VentaRepository, ProductoRepository
from ..domain.exception import StockInsuficienteError, ProductoNoEncontradoError, VentaNoEncontradaError

class VentaService:
    def __init__(self, venta_repository: VentaRepository, producto_repository: ProductoRepository):
        self.venta_repository = venta_repository
        self.producto_repository = producto_repository
    
    async def crear_venta(self, detalles: List[Dict[str, Any]], usuario_id: Optional[int] = None) -> Venta:
        """
        Crea una nueva venta validando stock y precios
        """
        # Validar y obtener productos
        productos_validados = []
        total_venta = Decimal('0.00')
        
        for detalle in detalles:
            producto_id = detalle['producto_id']
            cantidad = detalle['cantidad']
            
            # Obtener producto - Asegúrate de usar await si es async
            producto = await self.producto_repository.get_by_id(producto_id)
            if not producto:
                raise ProductoNoEncontradoError(producto_id)
            
            # Validar stock
            if producto.stock < cantidad:
                raise StockInsuficienteError(
                    producto.nombre, 
                    producto.stock, 
                    cantidad
                )
            
            # Calcular subtotal
            subtotal = producto.precio * cantidad
            total_venta += subtotal
            
            # Crear detalle de venta
            detalle_venta = DetalleVenta(
                id=None,
                producto_id=producto_id,
                producto_nombre=producto.nombre,
                cantidad=cantidad,
                precio=producto.precio,
                subtotal=subtotal
            )
            productos_validados.append(detalle_venta)
            
            # Actualizar stock (reducir) - Asegúrate de usar await si es async
            await self.producto_repository.update_stock(producto_id, -cantidad)
        
        # Crear venta
        venta = Venta(
            id=None,
            fecha=datetime.now(),
            total=total_venta,
            usuario_id=usuario_id,
            usuario_nombre=None,
            detalles=productos_validados
        )
        
        # Guardar venta - Asegúrate de usar await si es async
        venta_guardada = await self.venta_repository.save(venta)
        return venta_guardada
    
    async def obtener_venta(self, venta_id: int) -> Optional[Venta]:
        return await self.venta_repository.get_by_id(venta_id)
    
    async def obtener_ventas(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        print("🔍 [SERVICE] === OBTENER_VENTAS ===")
        try:
            print(f"🔍 [SERVICE] 1. Llamando a repositorio - skip: {skip}, limit: {limit}")
            ventas = await self.venta_repository.get_all(skip, limit)
            print(f"✅ [SERVICE] 2. Repositorio retornó: {len(ventas)} ventas")
            
            # Si el repositorio retorna diccionarios, procesarlos como tal
            for venta in ventas:
                print(f"Venta ID: {venta['id']}")  # Usar como diccionario
                for detalle in venta['detalles']:
                    print(f"  - Producto: {detalle['producto_nombre']}")
            
            return ventas
        except Exception as e:
            print(f"❌ [SERVICE] ERROR en obtener_ventas: {str(e)}")
            raise
    
    async def eliminar_venta(self, venta_id: int) -> bool:
        # Primero obtener la venta para restaurar stock
        venta = await self.venta_repository.get_by_id(venta_id)
        if not venta:
            return False
        
        # Restaurar stock de cada producto
        for detalle in venta.detalles:
            await self.producto_repository.update_stock(detalle.producto_id, detalle.cantidad)
        
        # Eliminar venta
        return await self.venta_repository.delete(venta_id)
    
    async def obtener_ventas_por_fecha(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Venta]:
        return await self.venta_repository.get_by_fecha_range(fecha_inicio, fecha_fin)
    
    async def obtener_ventas_por_producto(self, producto_id: int) -> List[Venta]:
        return await self.venta_repository.get_by_producto(producto_id)
    
    async def obtener_estadisticas(self) -> EstadisticasVentas:
        return await self.venta_repository.get_estadisticas()