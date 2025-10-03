from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime, timedelta

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/mydb"

Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class BadAttemptModel(Base):
    __tablename__ = "bad_attempts"
    ip = Column(String, primary_key=True)
    route = Column(String, primary_key=True)
    attempts = Column(Integer, default=0)
    window_expires_at = Column(DateTime, default=datetime.utcnow)
    last_attempt = Column(DateTime, default=datetime.utcnow)


class BlockedIPModel(Base):
    __tablename__ = "blocked_ips"
    ip = Column(String, primary_key=True)
    blocked_until = Column(DateTime)
    reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
