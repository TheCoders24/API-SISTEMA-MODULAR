from pydantic_settings import BaseSettings
from pydantic import PostgresDsn
from typing import List, Optional
import secrets
import json

class Settings(BaseSettings):
    # Base
    PROJECT_NAME: str = "WebSocket Notification System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    DEV_SECRET: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEV_TOKEN_LIFETIME: Optional[int] = None
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: Optional[PostgresDsn] = None
    SQLALCHEMY_DATABASE_URL: Optional[str] = None
    MONGODB_URL_DATABASE: Optional[str] = None
    MONGO_URI_APIKEYS: Optional[str] = None
    DB_POOL_MIN: int = 1
    DB_POOL_MAX: int = 20

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 25
    WS_TIMEOUT: int = 30
    WS_MAX_CONNECTIONS: int = 1000

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            def parse_env_settings(settings):
                if 'CORS_ORIGINS' in settings:
                    settings['CORS_ORIGINS'] = json.loads(settings['CORS_ORIGINS'])
                return settings
            return (init_settings, parse_env_settings, file_secret_settings)
settings = Settings()
