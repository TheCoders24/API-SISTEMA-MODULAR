from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from ..domain.entities import Venta, DetalleVenta, ProductoVenta, EstadisticasVentas
from ..domain.repositories import VentaRepository, ProductoRepository
from ..domain.exception import StockInsuficienteError, ProductoNoEncontradoError, VentaNoEncontradaError

class SQLVentaRepository(VentaRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, venta_id: int) -> Optional[Venta]:
        from .models import Venta as VentaModel, DetalleVenta as DetalleVentaModel, Producto, Usuario
        
        # Consulta principal de la venta
        result = await self.db.execute(
            select(VentaModel)
            .where(VentaModel.id == venta_id)
        )
        venta_model = result.scalar_one_or_none()
        
        if not venta_model:
            return None
        
        # Cargar detalles con productos usando join
        detalles_result = await self.db.execute(
            select(DetalleVentaModel, Producto)
            .join(Producto, DetalleVentaModel.producto_id == Producto.id)
            .where(DetalleVentaModel.venta_id == venta_id)
        )
        detalles_data = detalles_result.all()
        
        detalles = []
        for detalle_model, producto in detalles_data:
            detalles.append(DetalleVenta(
                id=detalle_model.id,
                producto_id=detalle_model.producto_id,
                producto_nombre=producto.nombre if producto else "Producto no encontrado",
                cantidad=detalle_model.cantidad,
                precio=detalle_model.precio,
                subtotal=detalle_model.cantidad * detalle_model.precio
            ))
        
        # Cargar usuario si existe
        usuario_nombre = "Sistema"
        if venta_model.usuario_id:
            usuario_result = await self.db.execute(
                select(Usuario)
                .where(Usuario.id == venta_model.usuario_id)
            )
            usuario = usuario_result.scalar_one_or_none()
            usuario_nombre = usuario.nombre if usuario else "Sistema"
        
        return Venta(
            id=venta_model.id,
            fecha=venta_model.fecha,
            total=venta_model.total,
            usuario_id=venta_model.usuario_id,
            usuario_nombre=usuario_nombre,
            detalles=detalles
        )
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        print("🔍 [REPOSITORY] === GET_ALL VENTAS ===")
        try:
            from .models import Venta as VentaModel, DetalleVenta as DetalleVentaModel, Producto, Usuario
            
            print("🔍 [REPOSITORY] 1. Importando modelos...")
            
            # Consulta principal
            print("🔍 [REPOSITORY] 2. Ejecutando consulta principal...")
            result = await self.db.execute(
                select(VentaModel)
                .order_by(VentaModel.fecha.desc())
                .offset(skip)
                .limit(limit)
            )
            ventas_models = result.scalars().all()
            print(f"✅ [REPOSITORY] 3. Consulta principal retornó: {len(ventas_models)} ventas_models")
            
            if not ventas_models:
                print("ℹ️  [REPOSITORY] No hay ventas en la base de datos")
                return []
            
            ventas = []
            for i, venta_model in enumerate(ventas_models):
                print(f"🔍 [REPOSITORY] 4.{i+1} Procesando venta ID: {venta_model.id}")
                
                # Cargar detalles
                print(f"🔍 [REPOSITORY] 5.{i+1} Cargando detalles para venta {venta_model.id}...")
                detalles_result = await self.db.execute(
                    select(DetalleVentaModel, Producto)
                    .join(Producto, DetalleVentaModel.producto_id == Producto.id)
                    .where(DetalleVentaModel.venta_id == venta_model.id)
                )
                detalles_data = detalles_result.all()
                print(f"✅ [REPOSITORY] 6.{i+1} Venta {venta_model.id} tiene {len(detalles_data)} detalles")
                
                detalles = []
                for detalle_model, producto in detalles_data:
                    detalles.append({
                        "id": detalle_model.id,
                        "producto_id": detalle_model.producto_id,
                        "producto_nombre": producto.nombre if producto else "Producto no encontrado",
                        "cantidad": detalle_model.cantidad,
                        "precio": float(detalle_model.precio),  # Convertir Decimal a float
                        "subtotal": float(detalle_model.cantidad * detalle_model.precio)  # Convertir Decimal a float
                    })
                
                # Cargar usuario
                usuario_nombre = "Sistema"
                if venta_model.usuario_id:
                    print(f"🔍 [REPOSITORY] 7.{i+1} Cargando usuario ID: {venta_model.usuario_id}")
                    usuario_result = await self.db.execute(
                        select(Usuario)
                        .where(Usuario.id == venta_model.usuario_id)
                    )
                    usuario = usuario_result.scalar_one_or_none()
                    usuario_nombre = usuario.nombre if usuario else "Sistema"
                
                venta = {
                    "id": venta_model.id,
                    "fecha": venta_model.fecha.isoformat() if hasattr(venta_model.fecha, 'isoformat') else str(venta_model.fecha),
                    "total": float(venta_model.total),  # Convertir Decimal a float
                    "usuario_id": venta_model.usuario_id,
                    "usuario_nombre": usuario_nombre,
                    "detalles": detalles
                }
                ventas.append(venta)
            
            print(f"✅ [REPOSITORY] 8. Retornando {len(ventas)} ventas procesadas")
            return ventas
            
        except Exception as e:
            print(f"❌ [REPOSITORY] ERROR en get_all: {str(e)}")
            import traceback
            print("❌ [REPOSITORY] Traceback completo:")
            traceback.print_exc()
            raise
    
    async def save(self, venta: Venta) -> Venta:
        from .models import Venta as VentaModel, DetalleVenta as DetalleVentaModel
        
        try:
            # Crear modelo de venta
            venta_model = VentaModel(
                total=venta.total,
                usuario_id=venta.usuario_id
            )
            self.db.add(venta_model)
            await self.db.flush()  # Para obtener el ID
            
            # Crear detalles
            for detalle in venta.detalles:
                detalle_model = DetalleVentaModel(
                    venta_id=venta_model.id,
                    producto_id=detalle.producto_id,
                    cantidad=detalle.cantidad,
                    precio=detalle.precio
                )
                self.db.add(detalle_model)
            
            await self.db.commit()
            
            # Recargar la venta para obtener relaciones
            result = await self.db.execute(
                select(VentaModel).where(VentaModel.id == venta_model.id)
            )
            venta_model_actualizada = result.scalar_one()
            
            # Actualizar ID de la venta
            venta.id = venta_model_actualizada.id
            return venta
            
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def delete(self, venta_id: int) -> bool:
        from .models import Venta as VentaModel
        
        result = await self.db.execute(
            select(VentaModel).where(VentaModel.id == venta_id)
        )
        venta_model = result.scalar_one_or_none()
        
        if not venta_model:
            return False
        
        await self.db.delete(venta_model)
        await self.db.commit()
        return True
    
    async def get_by_fecha_range(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Venta]:
        from .models import Venta as VentaModel
        
        result = await self.db.execute(
            select(VentaModel)
            .where(
                VentaModel.fecha >= fecha_inicio,
                VentaModel.fecha <= fecha_fin
            )
            .order_by(VentaModel.fecha.desc())
        )
        ventas_models = result.scalars().all()
        
        ventas = []
        for venta_model in ventas_models:
            venta = await self.get_by_id(venta_model.id)
            if venta:
                ventas.append(venta)
        
        return ventas
    
    async def get_by_producto(self, producto_id: int) -> List[Venta]:
        from .models import Venta as VentaModel, DetalleVenta as DetalleVentaModel
        
        # Obtener IDs de ventas que contienen el producto
        ventas_result = await self.db.execute(
            select(VentaModel.id)
            .join(DetalleVentaModel, VentaModel.id == DetalleVentaModel.venta_id)
            .where(DetalleVentaModel.producto_id == producto_id)
            .distinct()
        )
        venta_ids = ventas_result.scalars().all()
        
        ventas = []
        for venta_id in venta_ids:
            venta = await self.get_by_id(venta_id)
            if venta:
                ventas.append(venta)
        
        return ventas
    
    async def get_estadisticas(self) -> EstadisticasVentas:
        from .models import Venta as VentaModel, DetalleVenta as DetalleVentaModel
        
        hoy = date.today()
        
        try:
            # Estadísticas generales
            result_total_ventas = await self.db.execute(select(func.count(VentaModel.id)))
            total_ventas = result_total_ventas.scalar() or 0
            
            result_ingresos_totales = await self.db.execute(select(func.coalesce(func.sum(VentaModel.total), 0)))
            ingresos_totales = result_ingresos_totales.scalar() or Decimal('0.00')
            
            result_total_productos = await self.db.execute(select(func.coalesce(func.sum(DetalleVentaModel.cantidad), 0)))
            total_productos_vendidos = result_total_productos.scalar() or 0
            
            # Estadísticas de hoy
            result_ventas_hoy = await self.db.execute(
                select(func.count(VentaModel.id))
                .where(func.date(VentaModel.fecha) == hoy)
            )
            ventas_hoy = result_ventas_hoy.scalar() or 0
            
            result_ingresos_hoy = await self.db.execute(
                select(func.coalesce(func.sum(VentaModel.total), 0))
                .where(func.date(VentaModel.fecha) == hoy)
            )
            ingresos_hoy = result_ingresos_hoy.scalar() or Decimal('0.00')
            
            # Calcular promedio
            promedio_venta = ingresos_totales / total_ventas if total_ventas > 0 else Decimal('0.00')
            
            return EstadisticasVentas(
                total_ventas=total_ventas,
                ingresos_totales=ingresos_totales,
                promedio_venta=round(promedio_venta, 2),
                total_productos_vendidos=total_productos_vendidos,
                ventas_hoy=ventas_hoy,
                ingresos_hoy=ingresos_hoy
            )
            
        except Exception as e:
            print(f"Error en get_estadisticas: {e}")
            return EstadisticasVentas(
                total_ventas=0,
                ingresos_totales=Decimal('0.00'),
                promedio_venta=Decimal('0.00'),
                total_productos_vendidos=0,
                ventas_hoy=0,
                ingresos_hoy=Decimal('0.00')
            )

class SQLProductoRepository(ProductoRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, producto_id: int) -> Optional[ProductoVenta]:
        from .models import Producto as ProductoModel
        
        result = await self.db.execute(
            select(ProductoModel).where(ProductoModel.id == producto_id)
        )
        producto_model = result.scalar_one_or_none()
        
        if not producto_model:
            return None
        
        return ProductoVenta(
            id=producto_model.id,
            nombre=producto_model.nombre,
            precio=producto_model.precio,
            stock=producto_model.stock
        )
    
    async def update_stock(self, producto_id: int, cantidad: int) -> bool:
        from .models import Producto as ProductoModel
        
        result = await self.db.execute(
            select(ProductoModel).where(ProductoModel.id == producto_id)
        )
        producto_model = result.scalar_one_or_none()
        
        if not producto_model:
            return False
        
        producto_model.stock += cantidad
        await self.db.commit()
        return True