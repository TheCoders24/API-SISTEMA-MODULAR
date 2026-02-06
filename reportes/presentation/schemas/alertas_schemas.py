from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from ...domain.entities.Alertas import TipoAlerta, SeveridadAlerta

class AlertaResponse(BaseModel):
    id: str
    tipo: TipoAlerta
    titulo: str
    descripcion: str
    metrica_id: str
    severidad: SeveridadAlerta
    fecha_deteccion: datetime
    accion_recomendada: Optional[str] = None
    resuelta: bool

class AlertaCreateRequest(BaseModel):
    tipo: TipoAlerta
    titulo: str = Field(..., min_length=5, max_length=200)
    descripcion: str = Field(..., min_length=10, max_length=1000)
    metrica_id: str = Field(...)
    severidad: SeveridadAlerta
    accion_recomendada: Optional[str] = Field(None, max_length=500)

class EstadisticasAlertasResponse(BaseModel):
    total: int
    activas: int
    resueltas: int
    por_severidad: Dict[str, int]
    por_tipo: Dict[str, int]
    ultima_actualizacion: datetime

class AlertaResueltaResponse(BaseModel):
    id: str
    resuelta: bool
    mensaje: str