# metricas/repositories.py
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict
import random

from ..models.models import (
    TipooMetrica, Tendencia, Periodo, TipoGrafico,
    MetricaResumen, MetricaDetalle, GraficoMetrica,
    KPIDashboard, PuntoGrafico, SerieGrafico
)

class MetricasRepository:
    def __init__(self):
        self.metricas_resumen = []
        self.metricas_detalle = []
        self.graficos = []
        self.kpis = []
        self._inicializar_datos()
    
    def _inicializar_datos(self):
        """Inicializar con datos de ejemplo realistas"""
        self._inicializar_metricas_resumen()
        self._inicializar_metricas_detalle()
        self._inicializar_graficos()
        self._inicializar_kpis()
    
    def _inicializar_metricas_resumen(self):
        """Inicializar métricas de resumen"""
        self.metricas_resumen = [
            MetricaResumen(
                id="ventas_totales",
                nombre="Ventas Totales",
                valor="$124,580",
                cambio="+12.5%",
                tendencia=Tendencia.ASCENDENTE,
                icono="dollar-sign",
                color="blue",
                categoria="finanzas",
                descripcion="Total de ventas netas del período"
            ),
            MetricaResumen(
                id="usuarios_activos",
                nombre="Usuarios Activos",
                valor="3,842",
                cambio="+8.2%",
                tendencia=Tendencia.ASCENDENTE,
                icono="users",
                color="green",
                categoria="usuarios",
                descripcion="Usuarios activos en los últimos 30 días"
            ),
            MetricaResumen(
                id="tasa_conversion",
                nombre="Tasa de Conversión",
                valor="4.8%",
                cambio="+1.2%",
                tendencia=Tendencia.ASCENDENTE,
                icono="trending-up",
                color="purple",
                categoria="marketing",
                descripcion="Porcentaje de visitantes que realizan una acción"
            ),
            MetricaResumen(
                id="pedidos_totales",
                nombre="Pedidos Totales",
                valor="1,240",
                cambio="-2.1%",
                tendencia=Tendencia.DESCENDENTE,
                icono="shopping-cart",
                color="orange",
                categoria="operaciones",
                descripcion="Número total de pedidos procesados"
            ),
            MetricaResumen(
                id="ingresos_netos",
                nombre="Ingresos Netos",
                valor="$89,450",
                cambio="+15.3%",
                tendencia=Tendencia.ASCENDENTE,
                icono="credit-card",
                color="teal",
                categoria="finanzas",
                descripcion="Ingresos después de deducciones"
            ),
            MetricaResumen(
                id="retencion_clientes",
                nombre="Retención Clientes",
                valor="78.2%",
                cambio="+3.4%",
                tendencia=Tendencia.ASCENDENTE,
                icono="repeat",
                color="indigo",
                categoria="clientes",
                descripcion="Porcentaje de clientes que regresan"
            )
        ]
    
    def _inicializar_metricas_detalle(self):
        """Inicializar métricas detalladas"""
        self.metricas_detalle = [
            MetricaDetalle(
                id="ventas_totales",
                nombre="Ventas Totales",
                valor_actual=124580.75,
                valor_anterior=110654.30,
                cambio_porcentual=12.5,
                tendencia=Tendencia.ASCENDENTE,
                unidad="USD",
                meta=150000.00,
                progreso_meta=83.05,
                periodo_comparacion="mes_anterior",
                confianza=0.92,
                datos_historicos=self._generar_datos_historicos(124580.75, 30)
            ),
            MetricaDetalle(
                id="usuarios_activos",
                nombre="Usuarios Activos",
                valor_actual=3842,
                valor_anterior=3550,
                cambio_porcentual=8.2,
                tendencia=Tendencia.ASCENDENTE,
                unidad="usuarios",
                meta=4500,
                progreso_meta=85.38,
                periodo_comparacion="mes_anterior",
                confianza=0.88,
                datos_historicos=self._generar_datos_historicos(3842, 30, is_int=True)
            )
        ]
    
    def _inicializar_graficos(self):
        """Inicializar gráficos predeterminados"""
        self.graficos = [
            self._crear_grafico_ventas_temporales(),
            self._crear_grafico_usuarios_activos(),
            self._crear_grafico_ventas_categoria(),
            self._crear_grafico_conversion_canal()
        ]
    
    def _inicializar_kpis(self):
        """Inicializar KPIs del dashboard"""
        self.kpis = [
            KPIDashboard(
                id="kpi_ventas",
                nombre="Ventas por Usuario",
                valor=32.45,
                unidad="USD",
                objetivo=35.00,
                progreso=92.7,
                estado="bueno",
                tendencia=Tendencia.ASCENDENTE,
                alertas=[]
            ),
            KPIDashboard(
                id="kpi_conversion",
                nombre="Tasa Conversión Objetivo",
                valor=4.8,
                unidad="%",
                objetivo=5.0,
                progreso=96.0,
                estado="excelente",
                tendencia=Tendencia.ASCENDENTE,
                alertas=[]
            ),
            KPIDashboard(
                id="kpi_retencion",
                nombre="Retención Clientes",
                valor=78.2,
                unidad="%",
                objetivo=80.0,
                progreso=97.75,
                estado="bueno",
                tendencia=Tendencia.ASCENDENTE,
                alertas=[]
            )
        ]
    
    def _generar_datos_historicos(self, valor_actual: float, dias: int, is_int: bool = False) -> List[Dict[str, Any]]:
        """Generar datos históricos simulados"""
        datos = []
        fecha_base = datetime.utcnow() - timedelta(days=dias)
        
        for i in range(dias):
            factor = random.uniform(0.8, 1.2)
            valor = valor_actual * factor * (i / dias)  # Tendencia creciente
            if is_int:
                valor = int(valor)
            
            datos.append({
                "fecha": (fecha_base + timedelta(days=i)).isoformat(),
                "valor": round(valor, 2),
                "variacion": random.uniform(-5, 5)
            })
        
        return datos
    
    def _crear_grafico_ventas_temporales(self) -> GraficoMetrica:
        """Crear gráfico de ventas temporales"""
        datos = []
        fecha_base = datetime.utcnow() - timedelta(days=30)
        
        for i in range(30):
            fecha = fecha_base + timedelta(days=i)
            valor = random.uniform(3000, 6000)
            datos.append(PuntoGrafico(
                x=fecha,
                y=round(valor, 2),
                etiqueta=fecha.strftime("%d/%m")
            ))
        
        serie = SerieGrafico(
            nombre="Ventas Diarias",
            datos=datos,
            color="#3B82F6",
            tipo=TipoGrafico.LINEA,
            relleno=True
        )
        
        return GraficoMetrica(
            id="grafico_ventas",
            titulo="Ventas Diarias - Últimos 30 días",
            subtitulo="Tendencia de crecimiento del 12.5%",
            series=[serie],
            tipo=TipoGrafico.LINEA,
            configuracion={
                "mostrar_grid": True,
                "mostrar_leyenda": True,
                "animaciones": True
            }
        )
    
    def _crear_grafico_usuarios_activos(self) -> GraficoMetrica:
        """Crear gráfico de usuarios activos"""
        categorias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        datos = []
        
        for i, categoria in enumerate(categorias):
            valor = random.randint(2500, 4500)
            datos.append(PuntoGrafico(
                x=categoria,
                y=float(valor),
                etiqueta=categoria,
                color="#10B981" if valor > 3500 else "#EF4444"
            ))
        
        serie = SerieGrafico(
            nombre="Usuarios por Día",
            datos=datos,
            color="#10B981",
            tipo=TipoGrafico.BARRA
        )
        
        return GraficoMetrica(
            id="grafico_usuarios",
            titulo="Usuarios Activos por Día de la Semana",
            subtitulo="Promedio semanal: 3,842 usuarios",
            series=[serie],
            tipo=TipoGrafico.BARRA
        )
    
    def _crear_grafico_ventas_categoria(self) -> GraficoMetrica:
        """Crear gráfico de ventas por categoría"""
        categorias = ["Electrónica", "Ropa", "Hogar", "Alimentos", "Deportes", "Libros", "Juguetes"]
        colores = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#06B6D4"]
        
        series = []
        for categoria, color in zip(categorias, colores):
            datos = []
            for i in range(12):  # 12 meses
                valor = random.uniform(5000, 25000)
                datos.append(PuntoGrafico(
                    x=f"Mes {i+1}",
                    y=round(valor, 2),
                    etiqueta=categoria
                ))
            
            series.append(SerieGrafico(
                nombre=categoria,
                datos=datos,
                color=color,
                tipo=TipoGrafico.AREA
            ))
        
        return GraficoMetrica(
            id="grafico_categorias",
            titulo="Ventas por Categoría - Evolución Anual",
            subtitulo="Electrónica lidera con 35% del total",
            series=series,
            tipo=TipoGrafico.AREA
        )
    
    def _crear_grafico_conversion_canal(self) -> GraficoMetrica:
        """Crear gráfico de conversión por canal"""
        canales = [
            ("Búsqueda Orgánica", 15.2, "#3B82F6"),
            ("Redes Sociales", 12.8, "#10B981"),
            ("Email Marketing", 8.5, "#F59E0B"),
            ("Publicidad Paga", 22.4, "#EF4444"),
            ("Referidos", 6.3, "#8B5CF6"),
            ("Directo", 34.8, "#EC4899")
        ]
        
        datos = []
        for canal, porcentaje, color in canales:
            datos.append(PuntoGrafico(
                x=canal,
                y=porcentaje,
                etiqueta=f"{porcentaje}%",
                color=color
            ))
        
        serie = SerieGrafico(
            nombre="Conversión por Canal",
            datos=datos,
            color="#8B5CF6",
            tipo=TipoGrafico.PASTEL
        )
        
        return GraficoMetrica(
            id="grafico_conversion",
            titulo="Tasa de Conversión por Canal de Marketing",
            subtitulo="Tráfico directo tiene la mayor conversión",
            series=[serie],
            tipo=TipoGrafico.PASTEL
        )
    
    # Métodos de acceso a datos
    async def obtener_dashboard(self, periodo: Periodo = Periodo.MENSUAL) -> Dict[str, Any]:
        """Obtener dashboard completo"""
        return {
            "id": "dashboard_principal",
            "nombre": "Dashboard Principal",
            "descripcion": "Dashboard de métricas clave del negocio",
            "metricas_resumen": self.metricas_resumen,
            "metricas_detalle": self.metricas_detalle,
            "graficos": self.graficos,
            "kpis": self.kpis,
            "periodo": periodo,
            "fecha_actualizacion": datetime.utcnow(),
            "configuracion": {
                "layout": {"tipo": "grid", "columnas": 12},
                "metricas_visibles": [m.id for m in self.metricas_resumen],
                "tema": "claro",
                "actualizacion_automatica": True,
                "intervalo_actualizacion": 300
            },
            "analisis_insights": [
                {
                    "tipo": "positivo",
                    "titulo": "Crecimiento Sostenido",
                    "descripcion": "Las ventas muestran crecimiento constante del 12.5%",
                    "impacto": "alto",
                    "accion_recomendada": "Mantener estrategia actual"
                },
                {
                    "tipo": "advertencia",
                    "titulo": "Disminución en Pedidos",
                    "descripcion": "Los pedidos han disminuido un 2.1%",
                    "impacto": "medio",
                    "accion_recomendada": "Revisar proceso de checkout"
                }
            ]
        }
    
    async def obtener_metrica_detalle(self, metrica_id: str) -> Optional[MetricaDetalle]:
        """Obtener detalle de una métrica específica"""
        for metrica in self.metricas_detalle:
            if metrica.id == metrica_id:
                return metrica
        return None
    
    async def obtener_grafico(self, grafico_id: str) -> Optional[GraficoMetrica]:
        """Obtener un gráfico específico"""
        for grafico in self.graficos:
            if grafico.id == grafico_id:
                return grafico
        return None
    
    async def generar_serie_temporal(
        self, 
        metrica_id: str, 
        fecha_inicio: datetime, 
        fecha_fin: datetime
    ) -> Optional[Dict[str, Any]]:
        """Generar serie temporal para una métrica"""
        # En una implementación real, esto consultaría una base de datos
        dias = (fecha_fin - fecha_inicio).days
        if dias <= 0:
            return None
        
        datos = []
        for i in range(dias):
            fecha = fecha_inicio + timedelta(days=i)
            valor = random.uniform(1000, 5000)
            datos.append(PuntoGrafico(
                x=fecha,
                y=round(valor, 2),
                etiqueta=fecha.strftime("%d/%m")
            ))
        
        return {
            "metrica_id": metrica_id,
            "nombre": "Serie Temporal Generada",
            "datos": datos,
            "estadisticas": {
                "media": sum(p.y for p in datos) / len(datos),
                "maximo": max(p.y for p in datos),
                "minimo": min(p.y for p in datos),
                "desviacion": 1250.45
            },
            "tendencia": {
                "direccion": "ascendente",
                "fuerza": 0.78,
                "confianza": 0.92
            }
        }
    
    async def obtener_analisis_comparativo(
        self, 
        periodo1: Periodo, 
        periodo2: Periodo
    ) -> Dict[str, Any]:
        """Obtener análisis comparativo entre períodos"""
        return {
            "periodo_actual": {
                "tipo": periodo1.value,
                "fecha_inicio": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "fecha_fin": datetime.utcnow().isoformat()
            },
            "periodo_anterior": {
                "tipo": periodo2.value,
                "fecha_inicio": (datetime.utcnow() - timedelta(days=60)).isoformat(),
                "fecha_fin": (datetime.utcnow() - timedelta(days=30)).isoformat()
            },
            "comparativa": {
                "ventas": {"actual": 124580, "anterior": 110654, "cambio": 12.5},
                "usuarios": {"actual": 3842, "anterior": 3550, "cambio": 8.2},
                "conversion": {"actual": 4.8, "anterior": 4.2, "cambio": 14.3},
                "pedidos": {"actual": 1240, "anterior": 1265, "cambio": -2.0}
            },
            "metricas_mejoradas": ["ventas", "usuarios", "conversion"],
            "metricas_empeoradas": ["pedidos"],
            "recomendaciones": [
                {
                    "tipo": "optimizacion",
                    "descripcion": "Mejorar proceso de checkout para aumentar pedidos",
                    "prioridad": "alta"
                },
                {
                    "tipo": "mantenimiento",
                    "descripcion": "Continuar estrategia de crecimiento de usuarios",
                    "prioridad": "media"
                }
            ]
        }
    
    async def obtener_alertas(self) -> List[Dict[str, Any]]:
        """Obtener alertas activas"""
        return [
            {
                "id": "alerta_1",
                "tipo": "advertencia",
                "titulo": "Disminución en Pedidos",
                "descripcion": "Los pedidos han disminuido un 2.1% en el último mes",
                "metrica_id": "pedidos_totales",
                "valor_actual": 1240,
                "valor_umbral": 1300,
                "severidad": "media",
                "fecha_deteccion": datetime.utcnow().isoformat(),
                "estado": "activa",
                "accion_recomendada": "Revisar estrategia de ventas y checkout"
            },
            {
                "id": "alerta_2",
                "tipo": "informativo",
                "titulo": "Crecimiento en Ventas",
                "descripcion": "Las ventas superan la meta mensual",
                "metrica_id": "ventas_totales",
                "valor_actual": 124580,
                "valor_umbral": 120000,
                "severidad": "baja",
                "fecha_deteccion": datetime.utcnow().isoformat(),
                "estado": "activa",
                "accion_recomendada": "Analizar factores de éxito"
            }
        ]