# metricas/services.py
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import uuid

from ..models.models import (
    Periodo, TipoGrafico, DashboardCompleto, MetricaDetalle,
    GraficoMetrica, AnalisisComparativo, AlertaMetrica,
    SerieTemporalCompleta, FiltroMetricas
)

from .repository import MetricasRepository
#from metricas.models.models import PuntoGrafico, SerieGrafico
from ...metricas.models.models import PuntoGrafico, SerieGrafico
logger = logging.getLogger(__name__)

class MetricasService:
    def __init__(self):
        self.repository = MetricasRepository()
    
    async def obtener_dashboard(
        self, 
        periodo: Periodo = Periodo.MENSUAL,
        filtros: Optional[FiltroMetricas] = None
    ) -> DashboardCompleto:
        """Obtener dashboard completo de métricas"""
        try:
            datos = await self.repository.obtener_dashboard(periodo)
            
            # Aplicar filtros si existen
            if filtros:
                # Filtrar métricas según lo solicitado
                metricas_filtradas = [
                    m for m in datos["metricas_resumen"]
                    if m.categoria in (filtros.categorias or [m.categoria])
                ]
                if metricas_filtradas:
                    datos["metricas_resumen"] = metricas_filtradas
            
            return DashboardCompleto(**datos)
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard: {str(e)}")
            raise
    
    async def obtener_metrica_detalle(
        self, 
        metrica_id: str
    ) -> Optional[MetricaDetalle]:
        """Obtener detalle de una métrica específica"""
        try:
            return await self.repository.obtener_metrica_detalle(metrica_id)
        except Exception as e:
            logger.error(f"Error obteniendo métrica {metrica_id}: {str(e)}")
            return None
    
    async def obtener_grafico(
        self, 
        grafico_id: str,
        personalizaciones: Optional[Dict[str, Any]] = None
    ) -> Optional[GraficoMetrica]:
        """Obtener un gráfico específico"""
        try:
            grafico = await self.repository.obtener_grafico(grafico_id)
            if grafico and personalizaciones:
                # Aplicar personalizaciones
                grafico.configuracion.update(personalizaciones)
            return grafico
        except Exception as e:
            logger.error(f"Error obteniendo gráfico {grafico_id}: {str(e)}")
            return None
    
    async def generar_grafico_personalizado(
        self,
        tipo: TipoGrafico,
        datos: List[Dict[str, Any]],
        configuracion: Dict[str, Any]
    ) -> GraficoMetrica:
        """Generar gráfico personalizado"""
        try:
            # Convertir datos a PuntoGrafico
            puntos = []
            for dato in datos:
                puntos.append(PuntoGrafico(
                    x=dato.get("x", ""),
                    y=dato.get("y", 0),
                    etiqueta=dato.get("etiqueta"),
                    color=dato.get("color"),
                    metadata=dato.get("metadata")
                ))
            
            serie = SerieGrafico(
                nombre=configuracion.get("nombre", "Serie Personalizada"),
                datos=puntos,
                color=configuracion.get("color", "#3B82F6"),
                tipo=tipo,
                relleno=configuracion.get("relleno", False)
            )
            
            return GraficoMetrica(
                id=str(uuid.uuid4()),
                titulo=configuracion.get("titulo", "Gráfico Personalizado"),
                subtitulo=configuracion.get("subtitulo"),
                series=[serie],
                tipo=tipo,
                configuracion=configuracion.get("configuracion", {})
            )
            
        except Exception as e:
            logger.error(f"Error generando gráfico personalizado: {str(e)}")
            raise
    
    async def obtener_serie_temporal(
        self,
        metrica_id: str,
        fecha_inicio: datetime,
        fecha_fin: datetime,
        incluir_prediccion: bool = False
    ) -> Optional[SerieTemporalCompleta]:
        """Obtener serie temporal con análisis"""
        try:
            datos = await self.repository.generar_serie_temporal(
                metrica_id, fecha_inicio, fecha_fin
            )
            if not datos:
                return None
            
            # Generar predicción si se solicita
            prediccion = None
            if incluir_prediccion:
                prediccion = await self._generar_prediccion(datos["datos"])
            
            return SerieTemporalCompleta(
                metrica_id=metrica_id,
                nombre=datos["nombre"],
                datos=datos["datos"],
                estadisticas=datos["estadisticas"],
                tendencia=datos["tendencia"],
                prediccion=prediccion
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo serie temporal: {str(e)}")
            return None
    
    async def obtener_analisis_comparativo(
        self,
        periodo1: Periodo,
        periodo2: Periodo
    ) -> AnalisisComparativo:
        """Obtener análisis comparativo"""
        try:
            datos = await self.repository.obtener_analisis_comparativo(periodo1, periodo2)
            return AnalisisComparativo(**datos)
        except Exception as e:
            logger.error(f"Error obteniendo análisis comparativo: {str(e)}")
            raise
    
    async def obtener_alertas(
        self,
        severidad: Optional[str] = None,
        estado: str = "activa"
    ) -> List[AlertaMetrica]:
        """Obtener alertas de métricas"""
        try:
            alertas_datos = await self.repository.obtener_alertas()
            
            # Filtrar por severidad si se especifica
            if severidad:
                alertas_datos = [a for a in alertas_datos if a["severidad"] == severidad]
            
            # Filtrar por estado
            alertas_datos = [a for a in alertas_datos if a["estado"] == estado]
            
            return [AlertaMetrica(**alerta) for alerta in alertas_datos]
            
        except Exception as e:
            logger.error(f"Error obteniendo alertas: {str(e)}")
            return []
    
    async def calcular_tendencia(
        self,
        datos: List[float],
        periodo: int = 7
    ) -> Dict[str, Any]:
        """Calcular tendencia de una serie de datos"""
        if len(datos) < 2:
            return {"direccion": "estable", "fuerza": 0, "confianza": 0}
        
        # Calcular regresión lineal simple
        n = len(datos)
        sum_x = sum(range(n))
        sum_y = sum(datos)
        sum_xy = sum(i * datos[i] for i in range(n))
        sum_x2 = sum(i**2 for i in range(n))
        
        try:
            pendiente = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
            
            # Determinar dirección
            if pendiente > 0.1:
                direccion = "ascendente"
            elif pendiente < -0.1:
                direccion = "descendente"
            else:
                direccion = "estable"
            
            # Calcular fuerza (valor absoluto de la pendiente normalizado)
            rango = max(datos) - min(datos) if max(datos) != min(datos) else 1
            fuerza = min(abs(pendiente) * 10 / rango, 1.0)
            
            # Calcular confianza basada en la varianza
            media = sum_y / n
            varianza = sum((d - media)**2 for d in datos) / n
            confianza = 1.0 / (1.0 + varianza / 1000)
            
            return {
                "direccion": direccion,
                "fuerza": round(fuerza, 3),
                "confianza": round(confianza, 3),
                "pendiente": round(pendiente, 4),
                "prediccion": round(datos[-1] + pendiente, 2)
            }
            
        except ZeroDivisionError:
            return {"direccion": "estable", "fuerza": 0, "confianza": 0}
    
    async def _generar_prediccion(
        self,
        datos: List[PuntoGrafico],
        dias_futuro: int = 7
    ) -> List[PuntoGrafico]:
        """Generar predicción simple basada en tendencia"""
        if len(datos) < 2:
            return []
        
        # Extraer valores Y
        valores = [p.y for p in datos]
        
        # Calcular tendencia
        tendencia = await self.calcular_tendencia(valores)
        pendiente = tendencia.get("pendiente", 0)
        
        # Generar predicción
        prediccion = []
        ultimo_x = datos[-1].x
        ultimo_y = valores[-1]
        
        for i in range(1, dias_futuro + 1):
            if isinstance(ultimo_x, datetime):
                nuevo_x = ultimo_x + timedelta(days=i)
            else:
                nuevo_x = f"Predicción {i}"
            
            nuevo_y = ultimo_y + pendiente * i
            
            prediccion.append(PuntoGrafico(
                x=nuevo_x,
                y=round(nuevo_y, 2),
                etiqueta=f"Predicción D+{i}",
                color="#9CA3AF"  # Color gris para predicción
            ))
        
        return prediccion