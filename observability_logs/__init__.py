"""
Módulo de Observabilidad y Logging - Core del sistema
====================================================
Proporciona trazabilidad, auditoría y monitoreo para toda la aplicación.
"""

import sys
from pathlib import Path

# 🔥 AUTO-CONFIGURACIÓN DE PATH - ESTO SIEMPRE FUNCIONA
_ROOT_DIR = Path(__file__).parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

__version__ = "1.0.0"
__author__ = "Sistema Modular"
__description__ = "Módulo global de observabilidad con MongoDB"

# ============================================================================
# EXPORTACIONES PRINCIPALES - TODO LO QUE EXPONE EL MÓDULO
# ============================================================================

# Domain - Entidades y Value Objects
from .domain.entities import LogEntry
from .domain.enums import LogLevel, LogCategory
from .domain.value_objects import TraceID, generate_trace_id
from .domain.events import (
    DomainEvent,
    LogCreated,
    SecurityAlertTriggered,
    AnomalyDetected
)

# Application - Servicios y Fábricas
from .application.service import ObservabilityLogService
from .application.factory import LogFactory
from .application.context import LogContext
from .application.alerts import SecurityAlertService, AlertRule
from .application.queries import LogQueryService

# Configuración
from .config import ObservabilityConfig

# ============================================================================
# INICIALIZACIÓN RÁPIDA (OPCIONAL)
# ============================================================================

def setup_default(config: ObservabilityConfig = None):
    """
    Configuración rápida del módulo con valores por defecto.
    Útil para pruebas y desarrollo rápido.
    """
    from .infrastructure.mongodb.connection import mongodb_connection
    from .infrastructure.mongodb.repository import MongoDBLogRepository
    
    if config is None:
        config = ObservabilityConfig()
    
    mongodb_connection.initialize(config)
    repository = MongoDBLogRepository()
    service = ObservabilityLogService(repository)
    
    return {
        "config": config,
        "repository": repository,
        "service": service,
        "connection": mongodb_connection
    }

# ============================================================================
# LISTA DE EXPORTACIONES PÚBLICAS
# ============================================================================

__all__ = [
    # Domain
    "LogEntry",
    "LogLevel",
    "LogCategory",
    "TraceID",
    "generate_trace_id",
    "DomainEvent",
    "LogCreated",
    "SecurityAlertTriggered",
    "AnomalyDetected",
    
    # Application
    "ObservabilityLogService",
    "LogFactory",
    "LogContext",
    "SecurityAlertService",
    "AlertRule",
    "LogQueryService",
    
    # Config
    "ObservabilityConfig",
    
    # Helpers
    "setup_default",
]

# ============================================================================
# LOG DE INICIALIZACIÓN (OPCIONAL)
# ============================================================================

import logging
logger = logging.getLogger(__name__)
logger.debug(f"Módulo observability_logs v{__version__} cargado correctamente")
logger.debug(f"Root directory: {_ROOT_DIR}")