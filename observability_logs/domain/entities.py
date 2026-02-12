from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from .value_objects import TraceID
from .enums import LogLevel, LogCategory


@dataclass
class LogEntry:
    """Entidad principal de log - INMUTABLE después de creada"""
    trace_id: str
    level: str
    category: str
    action: str
    message: str
    user_id: Optional[str] = None
    role: Optional[str] = None
    ip: Optional[str] = None
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: Optional[int] = None  # Solo para DB
    
    def __post_init__(self):
        """Validaciones al crear la entidad"""
        if not self.trace_id:
            raise ValueError("trace_id es requerido")
        if not self.action:
            raise ValueError("action es requerido")
        if not self.message:
            raise ValueError("message es requerido")
        
        # Validar que level sea válido
        try:
            LogLevel(self.level)
        except ValueError:
            raise ValueError(f"Level inválido: {self.level}")
        
        # Validar que category sea válida
        try:
            LogCategory(self.category)
        except ValueError:
            raise ValueError(f"Categoría inválida: {self.category}")