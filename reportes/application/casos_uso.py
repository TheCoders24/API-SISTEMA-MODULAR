# reportes/application/casos_uso.py
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import logging

from ..domain.entities import (
    Reporte, FiltroReporte,
    TipoReporte, EstadoReporte, FormatoExportacion, DatosReporte
)
from ..domain.repositories import ReporteRepository
from ..domain.services import GeneradorDatosService, ExportadorReporteService

logger = logging.getLogger(__name__)

class ReporteCreateDTO:
    def __init__(self, nombre: str, tipo: TipoReporte, descripcion: Optional[str] = None,
                 filtros: Optional[Dict[str, Any]] = None, formato_salida: FormatoExportacion = FormatoExportacion.PDF):
        self.nombre = nombre
        self.tipo = tipo
        self.descripcion = descripcion
        self.filtros = filtros
        self.formato_salida = formato_salida

class CrearReporteCasoUso:
    def __init__(self, reporte_repo: ReporteRepository):
        self.reporte_repo = reporte_repo
    
    async def ejecutar(self, datos: ReporteCreateDTO, usuario_id: str) -> Reporte:
        # Crear entidad Reporte
        filtro = FiltroReporte(**datos.filtros) if datos.filtros else None
        
        reporte = Reporte(
            id=str(uuid.uuid4()),
            nombre=datos.nombre,
            tipo=datos.tipo,
            descripcion=datos.descripcion,
            formato_salida=datos.formato_salida,
            filtros=filtro,
            usuario_id=usuario_id
        )
        
        # Guardar en repositorio
        reporte_creado = await self.reporte_repo.crear(reporte)
        
        # Iniciar generación asíncrona
        asyncio.create_task(self._generar_reporte_background(reporte_creado.id))
        
        return reporte_creado
    
    async def _generar_reporte_background(self, reporte_id: str):
        # Este método se implementaría en otro caso de uso
        pass

class ObtenerReportesCasoUso:
    def __init__(self, reporte_repo: ReporteRepository):
        self.reporte_repo = reporte_repo
    
    async def ejecutar(
        self,
        skip: int = 0,
        limit: int = 10,
        tipo: Optional[TipoReporte] = None,
        estado: Optional[EstadoReporte] = None,
        usuario_id: Optional[str] = None
    ) -> List[Reporte]:
        return await self.reporte_repo.obtener_todos(
            skip=skip,
            limit=limit,
            tipo=tipo,
            estado=estado,
            usuario_id=usuario_id
        )

class GenerarReporteCasoUso:
    def __init__(
        self,
        reporte_repo: ReporteRepository,
        generador_datos: GeneradorDatosService,
        exportador: ExportadorReporteService
    ):
        self.reporte_repo = reporte_repo
        self.generador_datos = generador_datos
        self.exportador = exportador
    
    async def ejecutar(self, reporte_id: str) -> Reporte:
        # Obtener reporte
        reporte = await self.reporte_repo.obtener_por_id(reporte_id)
        if not reporte:
            raise ValueError(f"Reporte {reporte_id} no encontrado")
        
        # Iniciar generación
        reporte.iniciar_generacion()
        await self.reporte_repo.actualizar_estado(reporte_id, EstadoReporte.GENERANDO)
        
        inicio = datetime.utcnow()
        
        try:
            # Generar datos según tipo
            filtros_dict = reporte.filtros.to_dict() if reporte.filtros else {}
            
            if reporte.tipo == TipoReporte.VENTAS:
                datos = await self.generador_datos.generar_datos_ventas(filtros_dict)
            elif reporte.tipo == TipoReporte.USUARIOS:
                datos = await self.generador_datos.generar_datos_usuarios(filtros_dict)
            elif reporte.tipo == TipoReporte.INVENTARIO:
                datos = await self.generador_datos.generar_datos_inventario(filtros_dict)
            else:
                datos = await self.generador_datos.generar_datos_generales(reporte.tipo.value, filtros_dict)
            
            # Exportar a formato requerido
            if reporte.formato_salida == FormatoExportacion.PDF:
                contenido = await self.exportador.exportar_a_pdf(datos, reporte)
            elif reporte.formato_salida == FormatoExportacion.EXCEL:
                contenido = await self.exportador.exportar_a_excel(datos, reporte)
            elif reporte.formato_salida == FormatoExportacion.CSV:
                contenido = await self.exportador.exportar_a_csv(datos, reporte)
            else:  # JSON
                contenido = await self.exportador.exportar_a_json(datos, reporte)
            
            # Calcular duración
            duracion = (datetime.utcnow() - inicio).total_seconds()
            
            # Simular URL de descarga (en producción sería S3, etc.)
            url_descarga = f"/api/reportes/{reporte.id}/descargar"
            tamaño_archivo = len(contenido) / 1024 / 1024  # Convertir a MB
            
            # Completar reporte
            reporte.completar_generacion(url_descarga, tamaño_archivo, duracion)
            await self.reporte_repo.actualizar(reporte_id, {
                "estado": EstadoReporte.COMPLETADO,
                "url_descarga": url_descarga,
                "tamaño_archivo": tamaño_archivo,
                "duracion_generacion": duracion,
                "fecha_completado": reporte.fecha_completado
            })
            
            return reporte
            
        except Exception as e:
            logger.error(f"Error generando reporte {reporte_id}: {str(e)}")
            
            # Marcar error
            reporte.marcar_error(str(e))
            await self.reporte_repo.actualizar(reporte_id, {
                "estado": EstadoReporte.ERROR,
                "error_mensaje": str(e)
            })
            
            raise

class ExportarReporteCasoUso:
    def __init__(self, reporte_repo: ReporteRepository):
        self.reporte_repo = reporte_repo
    
    async def ejecutar(self, reporte_id: str, formato: FormatoExportacion) -> Dict[str, Any]:
        reporte = await self.reporte_repo.obtener_por_id(reporte_id)
        
        if not reporte:
            raise ValueError(f"Reporte {reporte_id} no encontrado")
        
        if not reporte.es_descargable():
            raise ValueError(f"Reporte {reporte_id} no está disponible para descarga")
        
        # Incrementar contador de descargas
        await self.reporte_repo.incrementar_descargas(reporte_id)
        reporte.incrementar_descargas()
        
        return {
            "reporte": reporte,
            "content_type": self._obtener_content_type(formato),
            "nombre_archivo": f"{reporte.nombre}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{formato.value}"
        }
    
    def _obtener_content_type(self, formato: FormatoExportacion) -> str:
        tipos = {
            FormatoExportacion.PDF: "application/pdf",
            FormatoExportacion.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            FormatoExportacion.CSV: "text/csv",
            FormatoExportacion.JSON: "application/json"
        }
        return tipos.get(formato, "application/octet-stream")

class ObtenerEstadisticasCasoUso:
    def __init__(self, reporte_repo: ReporteRepository):
        self.reporte_repo = reporte_repo
    
    async def ejecutar(self) -> Dict[str, Any]:
        return await self.reporte_repo.obtener_estadisticas()
    

class ObtenerReportesCasoUso:
    def __init__(self, repositorio):
        self.repositorio = repositorio
    
    def ejecutar(self):
        return self.repositorio.obtener_todos()