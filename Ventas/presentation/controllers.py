from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, date

from ...database.session import get_db
from ..application.service import VentaService
from ..application.dto import CrearVentaDTO, VentaResponseDTO, EstadisticasResponseDTO
from ..infrastructure.repository import SQLVentaRepository, SQLProductoRepository
from ..domain.exception import StockInsuficienteError, ProductoNoEncontradoError, VentaNoEncontradaError

router = APIRouter(prefix="/ventas", tags=["ventas"])

# CORRECCIÓN: Usar AsyncSession en lugar de Session
async def get_venta_service(db: AsyncSession = Depends(get_db)) -> VentaService:
    venta_repository = SQLVentaRepository(db)
    producto_repository = SQLProductoRepository(db)
    return VentaService(venta_repository, producto_repository)

# ========== RUTAS FIJAS PRIMERO ==========

@router.get("/test-simple")
async def test_simple():
    """Endpoint simple sin base de datos"""
    print("✅ [TEST] /ventas/test-simple llamado")
    return {
        "status": "ok",
        "message": "Endpoint de ventas funcionando",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/estadisticas/totales", response_model=EstadisticasResponseDTO)
async def obtener_estadisticas(
    venta_service: VentaService = Depends(get_venta_service)
):
    """
    Obtener estadísticas de ventas
    """
    try:
        return await venta_service.obtener_estadisticas()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )

@router.get("/fecha/rango/", response_model=List[VentaResponseDTO])
async def ventas_por_fecha(  # CORRECCIÓN: Agregar async
    fecha_inicio: date,
    fecha_fin: date,
    venta_service: VentaService = Depends(get_venta_service)
):
    """
    Obtener ventas por rango de fechas
    """
    try:
        fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
        fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
        
        return await venta_service.obtener_ventas_por_fecha(fecha_inicio_dt, fecha_fin_dt)  # CORRECCIÓN: Agregar await
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ventas por fecha: {str(e)}"
        )

# ========== RUTA RAIZ ==========

@router.get("/listar_ventas", response_model=List[VentaResponseDTO])
async def listar_ventas(
    skip: int = 0,
    limit: int = 100,
    venta_service: VentaService = Depends(get_venta_service)
):
    """
    Obtener lista de ventas con paginación
    """
    print("🔍 [BACKEND] === INICIANDO LISTAR_VENTAS ===")
    try:
        print("🔍 [BACKEND] 1. Llamando a venta_service.obtener_ventas()")
        ventas = await venta_service.obtener_ventas(skip, limit)
        print(f"✅ [BACKEND] 2. Ventas obtenidas: {len(ventas)}")
        
        # Debug de la primera venta si existe - CORREGIDO para diccionarios
        if ventas:
            primera = ventas[0]
            print(f"📦 [BACKEND] 3. Primera venta - ID: {primera['id']}, Total: {primera['total']}")  # ✅ Usar ['id']
            print(f"📦 [BACKEND] 4. Detalles: {len(primera['detalles'])}")  # ✅ Usar ['detalles']
            if primera['detalles']:
                primer_detalle = primera['detalles'][0]
                print(f"📦 [BACKEND] 5. Primer detalle - Producto: {primer_detalle['producto_nombre']}")  # ✅ Usar ['producto_nombre']
        
        print("✅ [BACKEND] 6. Retornando ventas exitosamente")
        return ventas
        
    except Exception as e:
        print(f"❌ [BACKEND] ERROR en listar_ventas: {str(e)}")
        print(f"❌ [BACKEND] Tipo de error: {type(e).__name__}")
        import traceback
        print(f"❌ [BACKEND] Traceback completo:")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener ventas: {str(e)}"
        )

@router.post("/", response_model=dict)
async def crear_venta(
    venta_dto: CrearVentaDTO,
    venta_service: VentaService = Depends(get_venta_service)
):
    """
    Crear una nueva venta
    """
    try:
        venta = await venta_service.crear_venta(
            [detalle.dict() for detalle in venta_dto.detalles],
            venta_dto.usuario_id
        )
        
        return {
            "message": "Venta creada exitosamente",
            "venta_id": venta.id,
            "total": float(venta.total),
            "productos_vendidos": len(venta.detalles)
        }
        
    except (StockInsuficienteError, ProductoNoEncontradoError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear venta: {str(e)}"
        )

# ========== RUTAS CON PARÁMETROS (AL FINAL) ==========

@router.get("/{venta_id}", response_model=VentaResponseDTO)
async def obtener_venta(  # CORRECCIÓN: Agregar async
    venta_id: int,
    venta_service: VentaService = Depends(get_venta_service)
):
    """
    Obtener una venta específica por ID
    """
    try:
        venta = await venta_service.obtener_venta(venta_id)  # CORRECCIÓN: Agregar await
        if not venta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venta con ID {venta_id} no encontrada"
            )
        return venta
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener venta: {str(e)}"
        )

@router.delete("/{venta_id}")
async def eliminar_venta(  # CORRECCIÓN: Agregar async
    venta_id: int,
    venta_service: VentaService = Depends(get_venta_service)
):
    """
    Eliminar una venta
    """
    try:
        if not await venta_service.eliminar_venta(venta_id):  # CORRECCIÓN: Agregar await
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Venta con ID {venta_id} no encontrada"
            )
        
        return {"message": "Venta eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar venta: {str(e)}"
        )