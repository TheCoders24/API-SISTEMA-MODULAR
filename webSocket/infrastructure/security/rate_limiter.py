from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncio
import logging
from ....core.config import settings
from ..database.postgres_manager import postgres_manager

logger = logging.getLogger(__name__)

class RateLimiter:
    async def is_rate_limited(self, identifier: str, limit: int, period: int = 60) -> bool:
        """Check if rate limit is exceeded using PostgreSQL"""
        current_time = datetime.now()
        period_start = current_time - timedelta(seconds=period)
        
        try:
            async with postgres_manager.get_connection() as conn:
                # Clean old entries
                await conn.execute(
                    "DELETE FROM rate_limits WHERE period_end < $1",
                    current_time
                )
                
                # Count events in current period
                count = await conn.fetchval('''
                    SELECT SUM(count) FROM rate_limits 
                    WHERE identifier = $1 AND event_type = $2 
                    AND period_start >= $3
                ''', identifier, 'request', period_start)
                
                count = count or 0
                
                if count >= limit:
                    return True
                
                # Insert new rate limit entry
                await conn.execute('''
                    INSERT INTO rate_limits 
                    (identifier, event_type, period_start, period_end)
                    VALUES ($1, $2, $3, $4)
                ''', identifier, 'request', period_start, current_time)
                
                return False
                
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return False

rate_limiter = RateLimiter()