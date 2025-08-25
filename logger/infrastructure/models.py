# infrastructure/logger/models.py

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class LogLevel(str,Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"

class LogEntry(BaseModel):
    timestamp: datetime
    level: LogLevel
    error_type: str
    error_message: str
    endpoint: Optional[str] = None
    user_id: Optional[str] = None
    exception_type: Optional[str] = None
    exception_message: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    additional_context: Optional[Dict[str, Any]] = None
    traceback: Optional[str] = None

class LogConfig(BaseModel):
    logs_dir: str = "logs"
    max_log_size_mb: int = 10
    days_to_keep: int = 30
    log_level: LogLevel = LogLevel.ERROR