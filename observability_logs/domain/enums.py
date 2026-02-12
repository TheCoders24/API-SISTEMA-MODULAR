from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(str, Enum):
    AUTH = "auth"
    AUTHORIZATION = "authorization"
    INVENTORY = "inventory"
    SALES = "sales"
    SECURITY = "security"
    SYSTEM = "system"
    DATABASE = "database"
    API = "api"