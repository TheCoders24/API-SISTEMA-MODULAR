from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class DomainEvent:
    """Base para todos los eventos de dominio"""
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex, init=False)
    occurred_at: datetime = field(default_factory=datetime.utcnow, init=False)


@dataclass
class LogCreated(DomainEvent):
    """Evento disparado cuando se crea un log"""
    log_entry: Any
    context: Optional[Dict[str, Any]] = None


@dataclass
class SecurityAlertTriggered(DomainEvent):
    """Evento para alertas de seguridad"""
    alert_type: str
    severity: str
    log_entries: List[Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetected(DomainEvent):
    """Evento para comportamientos anómalos"""
    anomaly_type: str
    confidence: float
    evidence: Dict[str, Any]
    suggested_action: Optional[str] = None
