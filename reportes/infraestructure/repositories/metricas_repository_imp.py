import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
from ...domain.entities.metricas import (
    Dashboard, MetricaResumen, MetricaDetalle, Grafico, KPI, Insight,
    MetricasRealtime, DatoHistorico, Periodo, Tendencia
)
from ...domain.repositories.metricas_repository import MetricasRepository

class MetricasRepositoryImpl(MetricasRepository):
    def __init__(self):
        self.colores = ["blue", "green", "purple", "orange", "red", "yellow", "indigo", "pink"]
        self.iconos = ["dollar-sign", "users", "trending-up", "shopping-cart", "credit-card", "repeat", "target"]
    
    async def obtener_dashboard(self, periodo: Periodo, usuario_id: Optional[str] = None) -> Dashboard:
        """Obtener dashboard de métricas"""
        await asyncio.sleep(0.1)
        
        # Generar métricas de resumen
        metricas_resumen = [
            MetricaResumen(
                id="ventas_totales",
                nombre="Ventas Totales",
                valor=f"${random.randint(100000, 200000):,}",
                cambio=f"+{random.randint(5, 20)}.{random.randint(0, 9)}%",
                tendencia=random.choice(list(Tendencia)),
                icono="dollar-sign",
                color="blue",
                categoria="finanzas"
            ),
            MetricaResumen(
                id="usuarios_activos",
                nombre="Usuarios Activos",
                valor=f"{random.randint(3000, 5000):,}",
                cambio=f"+{random.randint(2, 10)}.{random.randint(0, 9)}%",
                tendencia=Tendencia.ASCENDENTE,
                icono="users",
                color="green",
                categoria="usuarios"
            ),
            MetricaResumen(
                id="tasa_conversion",
                nombre="Tasa de Conversión",
                valor=f"{random.uniform(3.5, 6.5):.1f}%",
                cambio=f"+{random.uniform(0.5, 2.5):.1f}%",
                tendencia=random.choice([Tendencia.ASCENDENTE, Tendencia.DESCENDENTE, Tendencia.ESTABLE]),
                icono="trending-up",
                color="purple",
                categoria="marketing"
            ),
            MetricaResumen(
                id="pedidos_totales",
                nombre="Pedidos Totales",
                valor=f"{random.randint(1000, 2000):,}",
                cambio=f"{random.choice(['+', '-'])}{random.randint(1, 5)}.{random.randint(0, 9)}%",
                tendencia=random.choice([Tendencia.ASCENDENTE, Tendencia.DESCENDENTE]),
                icono="shopping-cart",
                color="orange",
                categoria="operaciones"
            )
        ]
        
        # Métricas detalladas
        metricas_detalle = [
            MetricaDetalle(
                id="ventas_totales",
                nombre="Ventas Totales",
                valor_actual=random.uniform(100000, 200000),
                cambio_porcentual=random.uniform(5, 20),
                unidad="USD",
                meta=200000,
                progreso_meta=random.uniform(60, 95)
            ),
            MetricaDetalle(
                id="usuarios_activos",
                nombre="Usuarios Activos",
                valor_actual=random.uniform(3000, 5000),
                cambio_porcentual=random.uniform(2, 10),
                unidad="usuarios",
                meta=5000,
                progreso_meta=random.uniform(60, 95)
            )
        ]
        
        # Generar gráficos basados en el período
        if periodo == Periodo.MENSUAL:
            dias = 30
            titulo_ventas = "Ventas Diarias - Últimos 30 días"
        elif periodo == Periodo.SEMANAL:
            dias = 7
            titulo_ventas = "Ventas Diarias - Última semana"
        elif periodo == Periodo.ANUAL:
            dias = 12
            titulo_ventas = "Ventas Mensuales - Último año"
        else:
            dias = 24
            titulo_ventas = "Ventas por Hora - Últimas 24 horas"
        
        # Gráfico de ventas
        datos_actual = [random.uniform(3000, 5000) for _ in range(dias)]
        datos_anterior = [random.uniform(2500, 4000) for _ in range(dias)]
        
        grafico_ventas = Grafico(
            id="grafico_ventas",
            titulo=titulo_ventas,
            tipo="linea",
            series=[
                {
                    "nombre": "2024",
                    "datos": [{"x": f"Día {i+1}" if dias > 7 else f"Hora {i+1}", 
                              "y": datos_actual[i], 
                              "etiqueta": f"${datos_actual[i]:,.0f}"} 
                             for i in range(dias)],
                    "color": "#3B82F6"
                },
                {
                    "nombre": "2023",
                    "datos": [{"x": f"Día {i+1}" if dias > 7 else f"Hora {i+1}", 
                              "y": datos_anterior[i], 
                              "etiqueta": f"${datos_anterior[i]:,.0f}"} 
                             for i in range(dias)],
                    "color": "#10B981"
                }
            ]
        )
        
        # Gráfico de categorías
        categorias = ["Electrónica", "Ropa", "Hogar", "Alimentos", "Deportes"]
        valores = [35, 25, 20, 12, 8]
        
        grafico_categorias = Grafico(
            id="grafico_categorias",
            titulo="Ventas por Categoría",
            tipo="pastel",
            series=[
                {
                    "nombre": "Ventas",
                    "datos": [
                        {"x": categorias[i], "y": valores[i], "etiqueta": f"{valores[i]}%"}
                        for i in range(len(categorias))
                    ],
                    "color": "#8B5CF6"
                }
            ]
        )
        
        # KPIs
        kpis = [
            KPI(
                id="kpi_ventas",
                nombre="Ventas por Usuario",
                valor=32.45,
                unidad="USD",
                objetivo=35.0,
                progreso=92.7,
                estado="bueno"
            ),
            KPI(
                id="kpi_conversion",
                nombre="Tasa Conversión Objetivo",
                valor=4.8,
                unidad="%",
                objetivo=5.0,
                progreso=96.0,
                estado="excelente"
            )
        ]
        
        # Insights
        analisis_insights = [
            Insight(
                tipo="positivo",
                titulo="Crecimiento Sostenido",
                descripcion="Las ventas muestran crecimiento constante del 12.5%",
                impacto="alto"
            ),
            Insight(
                tipo="advertencia",
                titulo="Disminución en Pedidos",
                descripcion="Los pedidos han disminuido un 2.1%",
                impacto="medio"
            )
        ]
        
        return Dashboard(
            id="dashboard_principal",
            nombre="Dashboard Principal",
            metricas_resumen=metricas_resumen,
            metricas_detalle=metricas_detalle,
            graficos=[grafico_ventas, grafico_categorias],
            kpis=kpis,
            fecha_actualizacion=datetime.now(),
            analisis_insights=analisis_insights
        )
    
    async def obtener_metricas_realtime(self) -> MetricasRealtime:
        """Obtener métricas en tiempo real"""
        await asyncio.sleep(0.05)
        return MetricasRealtime(
            usuarios_conectados=random.randint(100, 500),
            pedidos_pendientes=random.randint(5, 50),
            tickets_soporte=random.randint(1, 20),
            tiempo_respuesta=random.uniform(0.5, 3.0),
            timestamp=datetime.now()
        )
    
    async def obtener_metricas_historicas(self, metrica_id: str, dias: int = 7) -> List[DatoHistorico]:
        """Obtener datos históricos de una métrica"""
        await asyncio.sleep(0.1)
        
        datos = []
        fecha_actual = datetime.now()
        
        for i in range(dias):
            fecha = fecha_actual - timedelta(days=dias - i - 1)
            datos.append(DatoHistorico(
                fecha=fecha.strftime("%Y-%m-%d"),
                valor=random.uniform(1000, 5000),
                cambio=random.uniform(-5, 10),
                meta=4000 if i % 2 == 0 else 4500
            ))
        
        return datos
    
    async def crear_kpi_config(self, nombre: str, metrica_id: str, objetivo: float, unidad: str) -> Dict[str, Any]:
        """Crear configuración de KPI"""
        await asyncio.sleep(0.1)
        return {
            "id": f"kpi_{random.randint(1000, 9999)}",
            "nombre": nombre,
            "metrica_id": metrica_id,
            "objetivo": objetivo,
            "unidad": unidad,
            "created_at": datetime.now().isoformat()
        }
    
    async def guardar_metrica_historica(self, metrica_id: str, valor: float, 
                                       cambio: float = 0.0, meta: Optional[float] = None):
        """Guardar métrica histórica"""
        pass