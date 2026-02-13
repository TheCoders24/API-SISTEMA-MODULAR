# observability_logs/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class ObservabilityConfig(BaseSettings):
    """Configuración - SOLO MongoDB"""
    
    mongodb_uri: str = Field(
        "mongodb://localhost:27017", 
        validation_alias="OBS_MONGODB_URI"
    )
    mongodb_database: str = Field(
        "observability_prod", 
        validation_alias="OBS_MONGODB_DATABASE"
    )
    mongodb_collection: str = Field(
        "observability_logs", 
        validation_alias="OBS_MONGODB_COLLECTION"
    )
    log_retention_days: int = Field(90, validation_alias="OBS_LOG_RETENTION_DAYS")
    ws_enabled: bool = Field(True, validation_alias="OBS_WS_ENABLED")
    ws_max_connections: int = Field(1000, validation_alias="OBS_WS_MAX_CONNECTIONS")
    alerts_enabled: bool = Field(True, validation_alias="OBS_ALERTS_ENABLED")
    alert_check_interval: int = Field(60, validation_alias="OBS_ALERT_CHECK_INTERVAL")

    # 🔥 SOLUCIÓN: Añadir "extra": "ignore" para que no explote con variables de otras DBs
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 👈 Crucial: ignora DATABASE_URL, SECRET_KEY, etc.
    )