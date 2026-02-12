"""MongoDB Infrastructure - Repositorio y conexión"""

from .connection import mongodb_connection
from .repository import MongoDBLogRepository

__all__ = [
    "mongodb_connection",
    "MongoDBLogRepository",
]