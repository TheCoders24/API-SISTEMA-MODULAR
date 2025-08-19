import asyncpg
from ....database.session import get_db

async def get_db_connection():
    return await asyncpg.connect(get_db)