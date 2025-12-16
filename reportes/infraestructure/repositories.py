# reportes/infrastructure/repositories.py
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from ..domain.entities import Reporte, TipoReporte, EstadoReporte, FiltroReporte
from ..domain.repositories import ReporteRepository

class ReporteRepositoryMemoria(ReporteRepository):
    def __init__(self):
        self.reportes = {}
        self._inicializar_datos_ejemplo()
    
    def _inicializar_datos_ejemplo(self):
        # Datos de ejemplo
        reportes_ejemplo = [
            Reporte(
                id="1",
                nombre="Reporte de Ventas Mensual",
                tipo=TipoReporte.VENTAS,
                descripcion="Análisis de ventas del mes actual",
                estado=EstadoReporte.COMPLETADO,
                formato_salida="pdf",
                filtros=FiltroReporte(intervalo="mensual"),
                fecha_creacion=datetime(2024, 3, 15),
                fecha_completado=datetime(2024, 3, 15, 10, 30),
                descargas=142,
                url_descarga="/api/reportes/1/descargar",
                tamaño_archivo=2.5,
                duracion_generacion=15.2
            ),
            Reporte(
                id="2",
                nombre="Análisis de Usuarios Activos",
                tipo=TipoReporte.USUARIOS,
                estado=EstadoReporte.COMPLETADO,
                fecha_creacion=datetime(2024, 3, 14),
                fecha_completado=datetime(2024, 3, 14, 14, 20),
                descargas=89,
                url_descarga="/api/reportes/2/descargar",
                tamaño_archivo=1.8,
                duracion_generacion=8.5
            ),
            Reporte(
                id="3",
                nombre="Conversión por Canal",
                tipo=TipoReporte.MARKETING,
                estado=EstadoReporte.GENERANDO,
                fecha_creacion=datetime(2024, 3, 13)
            ),
            # Agrega más reportes de ejemplo...
        ]
        
        for reporte in reportes_ejemplo:
            self.reportes[reporte.id] = reporte
    
    async def obtener_por_id(self, reporte_id: str) -> Optional[Reporte]:
        return self.reportes.get(reporte_id)
    
    async def obtener_todos(
        self,
        skip: int = 0,
        limit: int = 10,
        tipo: Optional[TipoReporte] = None,
        estado: Optional[EstadoReporte] = None,
        usuario_id: Optional[str] = None
    ) -> List[Reporte]:
        reportes_filtrados = list(self.reportes.values())
        
        # Aplicar filtros
        if tipo:
            reportes_filtrados = [r for r in reportes_filtrados if r.tipo == tipo]
        
        if estado:
            reportes_filtrados = [r for r in reportes_filtrados if r.estado == estado]
        
        if usuario_id:
            reportes_filtrados = [r for r in reportes_filtrados if r.usuario_id == usuario_id]
        
        # Ordenar por fecha de creación (más reciente primero)
        reportes_filtrados.sort(key=lambda x: x.fecha_creacion, reverse=True)
        
        # Paginar
        return reportes_filtrados[skip:skip + limit]
    
    async def crear(self, reporte: Reporte) -> Reporte:
        self.reportes[reporte.id] = reporte
        return reporte
    
    async def actualizar(self, reporte_id: str, updates: Dict[str, Any]) -> Optional[Reporte]:
        if reporte_id not in self.reportes:
            return None
        
        reporte = self.reportes[reporte_id]
        
        # Actualizar campos
        for key, value in updates.items():
            if hasattr(reporte, key):
                setattr(reporte, key, value)
        
        reporte.fecha_actualizacion = datetime.utcnow()
        self.reportes[reporte_id] = reporte
        
        return reporte
    
    async def eliminar(self, reporte_id: str) -> bool:
        if reporte_id in self.reportes:
            del self.reportes[reporte_id]
            return True
        return False
    
    async def actualizar_estado(self, reporte_id: str, estado: EstadoReporte) -> bool:
        reporte = await self.obtener_por_id(reporte_id)
        if reporte:
            reporte.estado = estado
            reporte.fecha_actualizacion = datetime.utcnow()
            return True
        return False
    
    async def incrementar_descargas(self, reporte_id: str) -> bool:
        reporte = await self.obtener_por_id(reporte_id)
        if reporte:
            reporte.descargas += 1
            reporte.fecha_actualizacion = datetime.utcnow()
            return True
        return False
    
    async def obtener_estadisticas(self) -> Dict[str, Any]:
        total = len(self.reportes)
        completados = sum(1 for r in self.reportes.values() if r.estado == EstadoReporte.COMPLETADO)
        generando = sum(1 for r in self.reportes.values() if r.estado == EstadoReporte.GENERANDO)
        pendientes = sum(1 for r in self.reportes.values() if r.estado == EstadoReporte.PENDIENTE)
        
        # Estadísticas por tipo
        por_tipo = defaultdict(int)
        for reporte in self.reportes.values():
            por_tipo[reporte.tipo.value] += 1
        
        # Reportes más descargados
        mas_descargados = sorted(
            self.reportes.values(),
            key=lambda x: x.descargas,
            reverse=True
        )[:5]
        
        return {
            "total_reportes": total,
            "reportes_completados": completados,
            "reportes_generando": generando,
            "reportes_pendientes": pendientes,
            "descargas_totales": sum(r.descargas for r in self.reportes.values()),
            "tamaño_total_archivos": sum(r.tamaño_archivo or 0 for r in self.reportes.values()),
            "reportes_por_tipo": dict(por_tipo),
            "reportes_mas_descargados": [
                {
                    "id": r.id,
                    "nombre": r.nombre,
                    "tipo": r.tipo.value,
                    "descargas": r.descargas
                }
                for r in mas_descargados
            ]
        }