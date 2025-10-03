from datetime import datetime

class  BadAttempt:
    def __init__(self, ip: str, route: str, attempts: int = 0, window_expires_at: datetime = None):
        self.ip = ip
        self.route = route
        self.attempts = attempts
        self.window_expires_at = window_expires_at or datetime.utcnow()


class BlockedIP:
    def __init__(self, ip: str, blocked_until: datetime, reason: str = ""):
        self.ip = ip
        self.blocked_util = blocked_until
        self.reason = reason

class SuspiciousLog:
    def __init__(self, ip: str, route:str, method: str, pattern: str, playload_snippet: str, created_at: datetime = None):
        self.ip = ip
        self.route = route
        self.method = method
        self.pattern = pattern
        self.playload_snippet = playload_snippet
        self.created_at = created_at = datetime.utcnow()
        
        