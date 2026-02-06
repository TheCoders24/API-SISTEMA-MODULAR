from typing import List, Dict, Any, Optional
from ...application.use_cases.alertas_use_cases import (
    ObtenerAlertasActivasUseCase, CrearAlertaUseCase,
    ResolverAlertaUseCase, ObtenerEstadisticasAlertasUseCase
)
from ...infraestructure.repositories.alertas_repositories_imp import AlertasRepositoryImpl

class AlertasService:
    def __init__(self):
        self.alertas_repository = AlertasRepositoryImpl()
        self.obtener_alertas_uc = ObtenerAlertasActivasUseCase(self.alertas_repository)
        self.crear_alerta_uc = CrearAlertaUseCase(self.alertas_repository)
        self.resolver_alerta_uc = ResolverAlertaUseCase(self.alertas_repository)
        self.obtener_estadisticas_uc = ObtenerEstadisticasAlertasUseCase(self.alertas_repository)
    
    async def obtener_alertas_activas(self, severidad: Optional[str] = None, 
                                     tipo: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener alertas activas"""
        from ...domain.entities.Alertas import SeveridadAlerta, TipoAlerta

        severidad_enum = SeveridadAlerta(severidad) if severidad else None
        tipo_enum = TipoAlerta(tipo) if tipo else None
        
        alertas = await self.obtener_alertas_uc.execute(severidad_enum, tipo_enum)
        
        return [
            {
                "id": a.id,
                "tipo": a.tipo.value,
                "titulo": a.titulo,
                "descripcion": a.descripcion,
                "metrica_id": a.metrica_id,
                "severidad": a.severidad.value,
                "fecha_deteccion": a.fecha_deteccion.isoformat(),
                "accion_recomendada": a.accion_recomendada,
                "resuelta": a.resuelta
            }
            for a in alertas
        ]
    
    async def crear_alerta(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Crear una nueva alerta"""
        from ...domain.entities.Alertas import TipoAlerta, SeveridadAlerta
        
        alerta = await self.crear_alerta_uc.execute(
            tipo=TipoAlerta(datos["tipo"]),
            titulo=datos["titulo"],
            descripcion=datos["descripcion"],
            metrica_id=datos["metrica_id"],
            severidad=SeveridadAlerta(datos["severidad"]),
            accion_recomendada=datos.get("accion_recomendada")
        )
        
        return {
            "id": alerta.id,
            "tipo": alerta.tipo.value,
            "titulo": alerta.titulo,
            "descripcion": alerta.descripcion,
            "metrica_id": alerta.metrica_id,
            "severidad": alerta.severidad.value,
            "fecha_deteccion": alerta.fecha_deteccion.isoformat(),
            "accion_recomendada": alerta.accion_recomendada,
            "resuelta": alerta.resuelta
        }
    
    async def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtener estadísticas de alertas"""
        estadisticas = await self.obtener_estadisticas_uc.execute()
        
        return {
            "total": estadisticas.total,
            "activas": estadisticas.activas,
            "resueltas": estadisticas.resueltas,
            "por_severidad": estadisticas.por_severidad,
            "por_tipo": estadisticas.por_tipo,
            "ultima_actualizacion": estadisticas.ultima_actualizacion.isoformat()
        }
    
    async def resolver_alerta(self, alerta_id: str) -> Dict[str, Any]:
        """Resolver una alerta"""
        alerta = await self.resolver_alerta_uc.execute(alerta_id)
        
        return {
            "id": alerta.id,
            "tipo": alerta.tipo.value,
            "titulo": alerta.titulo,
            "descripcion": alerta.descripcion,
            "metrica_id": alerta.metrica_id,
            "severidad": alerta.severidad.value,
            "fecha_deteccion": alerta.fecha_deteccion.isoformat(),
            "accion_recomendada": alerta.accion_recomendada,
            "resuelta": alerta.resuelta
        }