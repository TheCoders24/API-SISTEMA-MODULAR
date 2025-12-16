# reportes/infrastructure/services.py
import json
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Any, List
import random

from ..domain.entities import DatosReporte, Reporte, FormatoExportacion
from ..domain.services import GeneradorDatosService, ExportadorReporteService

class GeneradorDatosMockService(GeneradorDatosService):
    async def generar_datos_ventas(self, filtros: Dict[str, Any]) -> DatosReporte:
        # Generar datos simulados para ventas
        fecha_inicio = filtros.get('fecha_inicio')
        fecha_fin = filtros.get('fecha_fin')
        
        categorias = ["Electrónica", "Ropa", "Hogar", "Alimentos", "Deportes"]
        ventas_por_categoria = {
            cat: random.uniform(10000, 50000) for cat in categorias
        }
        
        # Generar series temporales
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun"]
        ventas_mensuales = [
            {"mes": mes, "ventas": random.randint(50000, 100000), "objetivo": 75000}
            for mes in meses
        ]
        
        return DatosReporte(
            ventas_totales=sum(ventas_por_categoria.values()),
            ventas_por_categoria=ventas_por_categoria,
            usuarios_nuevos=random.randint(500, 1500),
            usuarios_activos=random.randint(3000, 5000),
            tasa_conversion=random.uniform(3.0, 6.0),
            pedidos_totales=random.randint(1000, 3000),
            metricas_temporales={
                "ventas_mensuales": ventas_mensuales,
                "ventas_diarias": [
                    {"dia": f"Día {i}", "ventas": random.randint(1000, 5000)}
                    for i in range(1, 8)
                ]
            }
        )
    
    async def generar_datos_usuarios(self, filtros: Dict[str, Any]) -> DatosReporte:
        # Datos simulados para usuarios
        return DatosReporte(
            usuarios_nuevos=random.randint(500, 1200),
            usuarios_activos=random.randint(3500, 4500),
            tasa_conversion=random.uniform(4.0, 7.0),
            metricas_temporales={
                "crecimiento_usuarios": [
                    {"semana": f"Semana {i}", "usuarios": random.randint(3000, 4500)}
                    for i in range(1, 9)
                ],
                "retencion": [
                    {"mes": mes, "retencion": random.uniform(70, 85)}
                    for mes in ["Ene", "Feb", "Mar", "Abr"]
                ]
            }
        )
    
    async def generar_datos_inventario(self, filtros: Dict[str, Any]) -> DatosReporte:
        # Datos simulados para inventario
        productos = ["Laptop", "Teléfono", "Tablet", "Monitor", "Teclado"]
        stock = {prod: random.randint(50, 500) for prod in productos}
        vendidos = {prod: random.randint(10, 200) for prod in productos}
        
        return DatosReporte(
            metricas_temporales={
                "inventario": [
                    {
                        "producto": prod,
                        "stock": stock[prod],
                        "vendidos": vendidos[prod],
                        "rotacion": vendidos[prod] / stock[prod] if stock[prod] > 0 else 0
                    }
                    for prod in productos
                ]
            }
        )
    
    async def generar_datos_generales(self, tipo: str, filtros: Dict[str, Any]) -> DatosReporte:
        # Datos genéricos para otros tipos
        return DatosReporte(
            ventas_totales=random.uniform(50000, 200000),
            usuarios_activos=random.randint(2000, 4000),
            tasa_conversion=random.uniform(2.5, 5.5)
        )

class ExportadorReporteService(ExportadorReporteService):
    async def exportar_a_pdf(self, datos: DatosReporte, reporte: Reporte) -> bytes:
        # En producción usarías reportlab, weasyprint, etc.
        # Por ahora simulamos con JSON
        contenido = {
            "reporte_id": reporte.id,
            "nombre": reporte.nombre,
            "tipo": reporte.tipo.value,
            "fecha_generacion": datetime.utcnow().isoformat(),
            "datos": datos.to_dict()
        }
        return json.dumps(contenido, indent=2, ensure_ascii=False).encode('utf-8')
    
    async def exportar_a_excel(self, datos: DatosReporte, reporte: Reporte) -> bytes:
        # Crear Excel con pandas
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de resumen
            resumen_data = {
                "Métrica": ["Ventas Totales", "Usuarios Activos", "Tasa Conversión", "Pedidos Totales"],
                "Valor": [
                    datos.ventas_totales or 0,
                    datos.usuarios_activos or 0,
                    datos.tasa_conversion or 0,
                    datos.pedidos_totales or 0
                ]
            }
            pd.DataFrame(resumen_data).to_excel(writer, sheet_name='Resumen', index=False)
            
            # Hoja de ventas por categoría
            if datos.ventas_por_categoria:
                ventas_data = {
                    "Categoría": list(datos.ventas_por_categoria.keys()),
                    "Ventas": list(datos.ventas_por_categoria.values())
                }
                pd.DataFrame(ventas_data).to_excel(writer, sheet_name='Ventas por Categoría', index=False)
        
        return output.getvalue()
    
    async def exportar_a_csv(self, datos: DatosReporte, reporte: Reporte) -> bytes:
        # Exportar a CSV
        output = BytesIO()
        
        # Crear DataFrame con datos principales
        df_data = []
        if datos.ventas_totales:
            df_data.append({"Métrica": "Ventas Totales", "Valor": datos.ventas_totales})
        if datos.usuarios_activos:
            df_data.append({"Métrica": "Usuarios Activos", "Valor": datos.usuarios_activos})
        if datos.tasa_conversion:
            df_data.append({"Métrica": "Tasa Conversión", "Valor": datos.tasa_conversion})
        
        df = pd.DataFrame(df_data)
        df.to_csv(output, index=False)
        
        return output.getvalue()
    
    async def exportar_a_json(self, datos: DatosReporte, reporte: Reporte) -> bytes:
        contenido = {
            "reporte_id": reporte.id,
            "nombre": reporte.nombre,
            "tipo": reporte.tipo.value,
            "fecha_generacion": datetime.utcnow().isoformat(),
            "datos": datos.to_dict()
        }
        return json.dumps(contenido, indent=2, ensure_ascii=False).encode('utf-8')