import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
from ...domain.entities.Alertas import Alerta, EstadisticasAlertas, TipoAlerta, SeveridadAlerta
from ...domain.repositories.alertas_repository import AlertasRepository

class AlertasRepositoryImpl(AlertasRepository):
    def __init__(self):
        self.alertas = self._generar_alertas_iniciales()
    
    def _generar_alertas_iniciales(self) -> List[Alerta]:
        """Generar alertas iniciales de ejemplo"""
        alertas = []
        
        metricas = ["ventas_totales", "usuarios_activos", "tasa_conversion", "pedidos_totales"]
        
        for i in range(1, 4):
            alertas.append(Alerta(
                id=f"alerta_{i}",
                tipo=random.choice(list(TipoAlerta)),
                titulo=f"Disminución en {random.choice(metricas).replace('_', ' ').title()}",
                descripcion=f"Se detectó una disminución del {random.randint(5, 20)}% en los últimos días",
                metrica_id=random.choice(metricas),
                severidad=random.choice(list(SeveridadAlerta)),
                fecha_deteccion=datetime.now() - timedelta(hours=random.randint(1, 72)),
                accion_recomendada=random.choice([
                    "Revisar estrategia de ventas",
                    "Verificar servidores",
                    "Contactar al equipo técnico",
                    "Revisar inventario"
                ])
            ))
        
        return alertas
    
    async def obtener_alertas_activas(self, severidad: Optional[SeveridadAlerta] = None,
                                     tipo: Optional[TipoAlerta] = None) -> List[Alerta]:
        """Obtener alertas activas"""
        await asyncio.sleep(0.05)
        
        alertas = [a for a in self.alertas if not a.resuelta]
        
        if severidad:
            alertas = [a for a in alertas if a.severidad == severidad]
        if tipo:
            alertas = [a for a in alertas if a.tipo == tipo]
        
        return alertas
    
    async def obtener_alerta_por_id(self, alerta_id: str) -> Optional[Alerta]:
        """Obtener alerta por ID"""
        await asyncio.sleep(0.05)
        for alerta in self.alertas:
            if alerta.id == alerta_id:
                return alerta
        return None
    
    async def crear_alerta(self, tipo: TipoAlerta, titulo: str, descripcion: str,
                          metrica_id: str, severidad: SeveridadAlerta,
                          accion_recomendada: Optional[str] = None) -> Alerta:
        """Crear una nueva alerta"""
        await asyncio.sleep(0.1)
        
        nueva_alerta = Alerta(
            id=f"alerta_{len(self.alertas) + 1}",
            tipo=tipo,
            titulo=titulo,
            descripcion=descripcion,
            metrica_id=metrica_id,
            severidad=severidad,
            fecha_deteccion=datetime.now(),
            accion_recomendada=accion_recomendada
        )
        
        self.alertas.append(nueva_alerta)
        return nueva_alerta
    
    async def resolver_alerta(self, alerta_id: str) -> Alerta:
        """Marcar una alerta como resuelta"""
        await asyncio.sleep(0.1)
        
        for alerta in self.alertas:
            if alerta.id == alerta_id:
                alerta.resuelta = True
                return alerta
        
        raise ValueError(f"Alerta con ID {alerta_id} no encontrada")
    
    async def obtener_estadisticas(self) -> EstadisticasAlertas:
        """Obtener estadísticas de alertas"""
        await asyncio.sleep(0.05)
        
        total = len(self.alertas)
        activas = len([a for a in self.alertas if not a.resuelta])
        resueltas = total - activas
        
        # Estadísticas por severidad
        por_severidad = {
            "alta": len([a for a in self.alertas if a.severidad == SeveridadAlerta.ALTA]),
            "media": len([a for a in self.alertas if a.severidad == SeveridadAlerta.MEDIA]),
            "baja": len([a for a in self.alertas if a.severidad == SeveridadAlerta.BAJA])
        }
        
        # Estadísticas por tipo
        por_tipo = {
            "advertencia": len([a for a in self.alertas if a.tipo == TipoAlerta.ADVERTENCIA]),
            "critica": len([a for a in self.alertas if a.tipo == TipoAlerta.CRITICA]),
            "informativa": len([a for a in self.alertas if a.tipo == TipoAlerta.INFORMATIVA])
        }
        
        return EstadisticasAlertas(
            total=total,
            activas=activas,
            resueltas=resueltas,
            por_severidad=por_severidad,
            por_tipo=por_tipo,
            ultima_actualizacion=datetime.now()
        )
    
    async def suscribir_notificaciones(self, callback):
        """Suscribirse a notificaciones de alertas"""
        pass