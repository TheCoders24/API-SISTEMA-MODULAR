from datetime import datetime
from typing import Optional, Dict, Any
from ..domain.entities import LogEntry
from ..domain.enums import LogLevel, LogCategory
from .context import LogContext


class LogFactory:
    """Factory para crear LogEntries de manera consistente"""
    
    @staticmethod
    def create(
        level: str,
        category: str,
        action: str,
        message: str,
        context: LogContext,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogEntry:
        """Crea un LogEntry a partir del contexto"""
        
        return LogEntry(
            trace_id=context.trace_id,
            level=level,
            category=category,
            action=action,
            message=message,
            user_id=context.user_id,
            role=context.role,
            ip=context.ip,
            endpoint=context.endpoint,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
    
    @staticmethod
    def create_system(
        action: str,
        message: str,
        context: LogContext,
        level: str = LogLevel.INFO,
        metadata: Optional[Dict] = None
    ) -> LogEntry:
        """Helper para logs del sistema"""
        return LogFactory.create(
            level=level,
            category=LogCategory.SYSTEM,
            action=action,
            message=message,
            context=context,
            metadata=metadata
        )
    
    @staticmethod
    def create_security(
        action: str,
        message: str,
        context: LogContext,
        level: str = LogLevel.WARNING,
        metadata: Optional[Dict] = None
    ) -> LogEntry:
        """Helper para logs de seguridad"""
        return LogFactory.create(
            level=level,
            category=LogCategory.SECURITY,
            action=action,
            message=message,
            context=context,
            metadata=metadata
        )