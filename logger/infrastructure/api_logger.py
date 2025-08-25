# infrastructure/logger/api_logger.py
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json
import traceback

# CORRECCIÓN: Importación relativa correcta y nombres de funciones correctos
from .models import LogLevel, LogConfig
from .logger.utils import sanitize_data, ensure_logs_dir, get_current_log_file, clean_old_logs, format_log_message

class APILogger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(APILogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializar el sistema de logging con configuración"""
        self.config = LogConfig()
        # CORRECCIÓN: ensure_logs_dir (no ensure_log_dir)
        self.logs_dir = ensure_logs_dir(self.config.logs_dir)
        
        # Configurar logging básico
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger = logging.getLogger("websocket_api")
        self._setup_file_handler()
        clean_old_logs(self.config.logs_dir, self.config.days_to_keep)
    
    def _setup_file_handler(self):
        """Configurar file handler para logs"""
        # CORRECCIÓN: get_current_log_file (no get_current_logs_file)
        log_file = get_current_log_file(self.config.logs_dir)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
            '%(pathname)s:%(lineno)d\n'
            '%(funcName)s\n'
            '-' * 50
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def log(
        self,
        level: LogLevel,
        error_type: str,
        error_message: str,
        exception: Optional[Exception] = None,
        endpoint: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """Método principal para loggear mensajes"""
        try:
            # Crear entrada de log
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level.value,
                "error_type": error_type,
                "error_message": error_message,
                "endpoint": endpoint,
                "user_id": user_id,
                "exception_type": type(exception).__name__ if exception else None,
                "exception_message": str(exception) if exception else None,
            }
            
            # Sanitizar y agregar request data
            if request_data:
                log_entry["request_data"] = sanitize_data(request_data)
            
            if additional_context:
                log_entry["additional_context"] = sanitize_data(additional_context)
            
            # Agregar traceback si hay excepción
            if exception:
                log_entry["traceback"] = traceback.format_exc()
            
            # Formatear y escribir el log
            log_message = format_log_message(log_entry)
            
            # Escribir según el nivel
            if level == LogLevel.ERROR:
                self.logger.error(log_message)
            elif level == LogLevel.WARNING:
                self.logger.warning(log_message)
            elif level == LogLevel.INFO:
                self.logger.info(log_message)
            elif level == LogLevel.DEBUG:
                self.logger.debug(log_message)
            
            # También loggear en consola
            print(f"{level.value}: {error_type} - {error_message}")
            
        except Exception as e:
            # Fallback en caso de error en el logging
            print(f"CRITICAL: Error in logger: {e}")
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        exception: Optional[Exception] = None,
        endpoint: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """Loggear error"""
        self.log(
            LogLevel.ERROR,
            error_type,
            error_message,
            exception,
            endpoint,
            request_data,
            user_id,
            additional_context
        )
    
    def log_warning(
        self,
        error_type: str,
        error_message: str,
        endpoint: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ):
        """Loggear warning"""
        self.log(
            LogLevel.WARNING,
            error_type,
            error_message,
            None,
            endpoint,
            request_data,
            user_id
        )
    
    def get_recent_errors(self, hours: int = 24) -> str:
        """Obtener errores recientes"""
        try:
            # CORRECCIÓN: get_current_log_file (no get_current_logs_file)
            log_file = get_current_log_file(self.config.logs_dir)
            if not log_file.exists():
                return "No hay errores recientes"
            
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            recent_errors = []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                current_error = []
                for line in f:
                    if line.startswith('TIMESTAMP:'):
                        try:
                            timestamp_str = line.split(':', 1)[1].strip()
                            error_time = datetime.fromisoformat(timestamp_str).timestamp()
                            if error_time >= cutoff_time:
                                current_error = [line]
                            else:
                                current_error = []
                        except:
                            current_error.append(line)
                    elif current_error:
                        current_error.append(line)
                        if line.strip() == "=" * 60:
                            recent_errors.append(''.join(current_error))
                            current_error = []
            
            return '\n'.join(recent_errors) if recent_errors else f"No hay errores en las últimas {hours} horas"
            
        except Exception as e:
            return f"Error obteniendo logs: {str(e)}"
    
    def get_log_files(self) -> list:
        """Obtener lista de archivos de log disponibles"""
        try:
            log_files = []
            for log_file in self.logs_dir.glob("api_errors_*.txt"):
                log_files.append({
                    "filename": log_file.name,
                    "size": log_file.stat().st_size,
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
            return sorted(log_files, key=lambda x: x["filename"], reverse=True)
        except Exception as e:
            self.log_error("LOG_FILES_ERROR", "Error listing log files", e)
            return []

# Instancia global del logger
api_logger = APILogger()