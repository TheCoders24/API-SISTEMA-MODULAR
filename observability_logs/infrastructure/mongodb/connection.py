from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional

from observability_logs.config import ObservabilityConfig


class MongoDBConnection:
    """Singleton para conexión a MongoDB"""

    _instance: Optional["MongoDBConnection"] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    _config: Optional[ObservabilityConfig] = None # 👈 Guardamos la config

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, config: ObservabilityConfig):
        """Inicializa la conexión a MongoDB"""
        self._config = config # 👈 Guardar referencia
        if self._client is None:
            self._client = MongoClient(config.mongodb_uri)
            self._db = self._client[config.mongodb_database]
            self._create_indexes(config)

    def _create_indexes(self, config: ObservabilityConfig):
        """Crea índices para búsquedas eficientes"""
        collection = self._db[config.mongodb_collection]

        # Índices simples
        collection.create_index([("trace_id", ASCENDING)])
        collection.create_index([("user_id", ASCENDING)])
        collection.create_index([("ip", ASCENDING)])
        collection.create_index([("timestamp", DESCENDING)])

        # Índices compuestos
        collection.create_index([("category", ASCENDING), ("timestamp", DESCENDING)])
        collection.create_index([("level", ASCENDING), ("timestamp", DESCENDING)])

        collection.create_index([
            ("user_id", ASCENDING),
            ("timestamp", DESCENDING)
        ])

        collection.create_index([
            ("ip", ASCENDING),
            ("timestamp", DESCENDING)
        ])

        # Índice de texto
        collection.create_index([
            ("message", TEXT),
            ("action", TEXT)
        ])

        # TTL (expiración automática)
        collection.create_index(
            "timestamp",
            expireAfterSeconds=config.log_retention_days * 86400
        )

    @property
    def db(self) -> Database:
        if self._db is None:
            raise RuntimeError("MongoDB no inicializado. Llama initialize() primero.")
        return self._db

    @property
    def logs(self) -> Collection:
        # ✅ Ahora usa el nombre correcto desde la config
        return self.db[self._get_collection_name()]

    def _get_collection_name(self) -> str:
        # ✅ Simplificado: Retorna el nombre configurado o uno por defecto
        if self._config:
            return self._config.mongodb_collection
        return "observability_logs"

    def is_connected(self) -> bool:
        try:
            # Forma recomendada de verificar conexión real en PyMongo
            if self._client:
                self._client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._config = None


# Singleton
mongodb_connection = MongoDBConnection()