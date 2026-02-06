from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

class TipoAlerta(str, Enum):
    ADVERTENCIA = "advertencia"
    CRITICA = "critica"
    INFORMATIVA = "informativa"

class SeveridadAlerta(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"

@dataclass
class Alerta:
    id: str
    tipo: TipoAlerta
    titulo: str
    descripcion: str
    metrica_id: str
    severidad: SeveridadAlerta
    fecha_deteccion: datetime
    accion_recomendada: Optional[str] = None
    resuelta: bool = False

@dataclass
class EstadisticasAlertas:
    total: int
    activas: int
    resueltas: int
    por_severidad: Dict[str, int]
    por_tipo: Dict[str, int]
    ultima_actualizacion: datetime