from ..infrastructure.repositories import BadAttemptRepository, BlockedIPRepository, LogRepository
import re

SUSPICIOUS_PATTERN = re.compile(r"\b(OR|UNION|SELECT|--|;|/\*|DROP|ALTER|<script>)\b", re.IGNORECASE)

def is_suspicious(payload: str) -> bool:
    return bool(SUSPICIOUS_PATTERN.search(payload))

class LogService:
    def __init__(self):
        self.bad_attempt_repo = BadAttemptRepository()
        self.blocked_ip_repo = BlockedIPRepository()
        self.log_repo = LogRepository()

    async def register_attempt(self, ip: str, route: str, payload: str):
        # PostgreSQL
        await self.bad_attempt_repo.increment(ip, route)
        attempts = await self.bad_attempt_repo.get_attempts(ip, route)
        if attempts >= 10:
            await self.blocked_ip_repo.block(ip)

        # MongoDB
        await self.log_repo.save_suspicious(ip, route, payload)

    async def is_ip_blocked(self, ip: str) -> bool:
        return await self.blocked_ip_repo.is_blocked(ip)
