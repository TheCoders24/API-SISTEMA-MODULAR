import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

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
        """Inicializa logger"""
        self.config = LogConfig()
        self.logs_dir = ensure_logs_dir(self.config.logs_dir)

        self.logger = logging.getLogger("websocket_api")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # Limpiar handlers previos
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        log_file = get_current_log_file(self.logs_dir)
        self.file_handler = logging.FileHandler(log_file, encoding="utf-8")
        self.file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s\n"
            "Path: %(pathname)s:%(lineno)d\n"
            "Func: %(funcName)s\n"
            + "-"*60
        )
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

        clean_old_logs(self.logs_dir, self.config.days_to_keep)
        print(f"[Logger inicializado] Archivo de log: {log_file}")

    def _write(self, level_func, log_entry: str):
        level_func(log_entry)
        for handler in self.logger.handlers:
            handler.flush()

    def log(
        self,
        level: LogLevel,
        error_type: str,
        error_message: str,
        exception: Optional[Exception] = None,
        endpoint: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ):
        try:
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

            if request_data:
                log_entry["request_data"] = sanitize_data(request_data)
            if additional_context:
                log_entry["additional_context"] = sanitize_data(additional_context)
            if exception:
                log_entry["traceback"] = traceback.format_exc()

            log_message = format_log_message(log_entry)
            if not log_message:
                log_message = str(log_entry)

            if level == LogLevel.ERROR:
                self._write(self.logger.error, log_message)
            elif level == LogLevel.WARNING:
                self._write(self.logger.warning, log_message)
            elif level == LogLevel.INFO:
                self._write(self.logger.info, log_message)
            else:
                self._write(self.logger.debug, log_message)

            print(f"[{level.value}] {error_type}: {error_message}")

        except Exception as e:
            print(f"❌ Error interno en logger: {e}")

    def log_error(self, error_type, error_message, exception=None, **kwargs):
        self.log(LogLevel.ERROR, error_type, error_message, exception, **kwargs)

    def log_warning(self, error_type, error_message, **kwargs):
        self.log(LogLevel.WARNING, error_type, error_message, **kwargs)

    def get_recent_errors(self, hours: int = 24) -> str:
        try:
            log_file = get_current_log_file(self.logs_dir)
            if not log_file.exists():
                return "No hay errores recientes"

            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            lines = []
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "[ERROR]" in line:
                        try:
                            timestamp_str = line.split(" ")[0]
                            if datetime.fromisoformat(timestamp_str).timestamp() >= cutoff_time:
                                lines.append(line)
                        except:
                            continue
            return "".join(lines) or f"No hay errores en las últimas {hours} horas"
        except Exception as e:
            return f"Error leyendo logs: {e}"

    def get_log_files(self) -> list:
        try:
            log_files = []
            for lf in self.logs_dir.glob("api_errors_*.txt"):
                log_files.append({
                    "filename": lf.name,
                    "size": lf.stat().st_size,
                    "modified": datetime.fromtimestamp(lf.stat().st_mtime).isoformat(),
                })
            return sorted(log_files, key=lambda x: x["filename"], reverse=True)
        except Exception as e:
            self.log_error("LOG_FILES_ERROR", "Error listando archivos", e)
            return []


api_logger = APILogger()
