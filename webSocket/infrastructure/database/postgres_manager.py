import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging
from datetime import datetime
from ....core.config import settings

logger = logging.getLogger(__name__)

class PostgreSQLManager:
    _pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                dsn=str(settings.DATABASE_URL),
                min_size=settings.DB_POOL_MIN,
                max_size=settings.DB_POOL_MAX,
                timeout=60,
                command_timeout=60,
            )
            
            # Initialize database schema
            await cls._initialize_schema(cls._pool)
            
        return cls._pool
    
    @classmethod
    async def _initialize_schema(cls, pool: asyncpg.Pool):
        """Initialize database tables"""
        async with pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    username VARCHAR(255),
                    email VARCHAR(255),
                    role VARCHAR(50) NOT NULL,
                    login_time TIMESTAMPTZ NOT NULL,
                    last_activity TIMESTAMPTZ NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    expires_at TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS connection_metrics (
                    id SERIAL PRIMARY KEY,
                    connection_id VARCHAR(255),
                    user_id VARCHAR(255),
                    channel VARCHAR(255) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    duration_ms INTEGER,
                    message_count INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS message_queue (
                    id SERIAL PRIMARY KEY,
                    message_id VARCHAR(255) UNIQUE NOT NULL,
                    channel VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    message_type VARCHAR(50) NOT NULL,
                    payload JSONB NOT NULL,
                    priority INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    scheduled_for TIMESTAMPTZ DEFAULT NOW(),
                    delivered_at TIMESTAMPTZ,
                    expires_at TIMESTAMPTZ
                );

                CREATE TABLE IF NOT EXISTS rate_limits (
                    id SERIAL PRIMARY KEY,
                    identifier VARCHAR(255) NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    count INTEGER DEFAULT 1,
                    period_start TIMESTAMPTZ NOT NULL,
                    period_end TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
                CREATE INDEX IF NOT EXISTS idx_connection_metrics_timestamp ON connection_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_message_queue_status ON message_queue(status);
                CREATE INDEX IF NOT EXISTS idx_message_queue_channel ON message_queue(channel);
                CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier ON rate_limits(identifier);
            ''')
    
    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncGenerator[asyncpg.Connection, None]:
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            try:
                yield connection
            finally:
                pass
    
    @classmethod
    async def close_pool(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

postgres_manager = PostgreSQLManager()
