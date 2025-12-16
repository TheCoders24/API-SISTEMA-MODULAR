# reportes/domain/services.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .entities import Reporte, DatosReporte, FormatoExportacion

class GeneradorDatosService(ABC):
    @abstractmethod
    async def generar_datos_ventas(self, filtros: Dict[str, Any]) -> DatosReporte:
        pass
    
    @abstractmethod
    async def generar_datos_usuarios(self, filtros: Dict[str, Any]) -> DatosReporte:
        pass
    
    @abstractmethod
    async def generar_datos_inventario(self, filtros: Dict[str, Any]) -> DatosReporte:
        pass
    
    @abstractmethod
    async def generar_datos_generales(self, tipo: str, filtros: Dict[str, Any]) -> DatosReporte:
        pass

class ExportadorReporteService(ABC):
    @abstractmethod
    async def exportar_a_pdf(self, datos: DatosReporte, reporte: Reporte) -> bytes:
        pass
    
    @abstractmethod
    async def exportar_a_excel(self, datos: DatosReporte, reporte: Reporte) -> bytes:
        pass
    
    @abstractmethod
    async def exportar_a_csv(self, datos: DatosReporte, reporte: Reporte) -> bytes:
        pass
    
    @abstractmethod
    async def exportar_a_json(self, datos: DatosReporte, reporte: Reporte) -> bytes:
        pass
    
    def obtener_content_type(self, formato: FormatoExportacion) -> str:
        tipos = {
            FormatoExportacion.PDF: "application/pdf",
            FormatoExportacion.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            FormatoExportacion.CSV: "text/csv",
            FormatoExportacion.JSON: "application/json"
        }
        return tipos.get(formato, "application/octet-stream")