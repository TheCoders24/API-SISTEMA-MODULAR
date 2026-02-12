from typing import List, Optional
from ..domain.entities import LogEntry
from ..domain.events import LogCreated


class ObservabilityLogService:
    """Servicio principal de logging - SIN LÓGICA DE NEGOCIO"""
    
    def __init__(self, repository, event_publisher=None):
        self.repository = repository
        self.event_publisher = event_publisher
    
    def write(self, log_entry: LogEntry) -> None:
        """Escribe un log y dispara evento"""
        # Guardar en repositorio
        saved_log = self.repository.save(log_entry)
        
        # Publicar evento si hay publisher
        if self.event_publisher:
            event = LogCreated(log_entry=saved_log)
            self.event_publisher.publish(event)
    
    def write_many(self, log_entries: List[LogEntry]) -> None:
        """Batch write para múltiples logs"""
        saved_logs = self.repository.save_many(log_entries)
        
        if self.event_publisher and saved_logs:
            for log in saved_logs:
                self.event_publisher.publish(LogCreated(log_entry=log))