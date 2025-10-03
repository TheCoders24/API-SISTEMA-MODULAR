from ..infrastructure.db_postgres import BadAttemptModel, BlockedIPModel, async_session
from ..infrastructure.db_mongo import db
from datetime import datetime, timedelta

ATTEMPT_WINDOW = timedelta(minutes=30)
ATTEMPT_THRESHOLD = 10
BLOCK_DURATION = timedelta(hours=1)

# PostgreSQL
class BadAttemptRepository:
    async def increment(self, ip: str, route: str):
        async with async_session() as session:
            attempt = await session.get(BadAttemptModel, {"ip": ip, "route": route})
            now = datetime.utcnow()
            if attempt:
                if attempt.window_expires_at < now:
                    attempt.attempts = 1
                    attempt.window_expires_at = now + ATTEMPT_WINDOW
                else:
                    attempt.attempts += 1
                attempt.last_attempt = now
            else:
                attempt = BadAttemptModel(
                    ip=ip,
                    route=route,
                    attempts=1,
                    window_expires_at=now + ATTEMPT_WINDOW,
                    last_attempt=now
                )
                session.add(attempt)
            await session.commit()

    async def get_attempts(self, ip: str, route: str) -> int:
        async with async_session() as session:
            attempt = await session.get(BadAttemptModel, {"ip": ip, "route": route})
            return attempt.attempts if attempt else 0

class BlockedIPRepository:
    async def block(self, ip: str):
        async with async_session() as session:
            now = datetime.utcnow()
            blocked = BlockedIPModel(
                ip=ip,
                blocked_until=now + BLOCK_DURATION,
                reason="Superó límite de intentos"
            )
            session.add(blocked)
            await session.commit()

    async def is_blocked(self, ip: str) -> bool:
        async with async_session() as session:
            blocked = await session.get(BlockedIPModel, {"ip": ip})
            if blocked and blocked.blocked_until > datetime.utcnow():
                return True
            return False

# MongoDB
class LogRepository:
    async def save_suspicious(self, ip: str, route: str, payload: str, method: str = "POST"):
        snippet = payload[:200]
        pattern = "SQL Injection / XSS"  # ejemplo básico
        log_entry = {
            "ip": ip,
            "route": route,
            "method": method,
            "pattern": pattern,
            "payload_snippet": snippet,
            "created_at": datetime.utcnow()
        }
        await db.suspicious_logs.insert_one(log_entry)
