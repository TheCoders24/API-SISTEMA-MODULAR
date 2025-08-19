from ..database.postgres_connection import get_db_connection
class PostgreSQLListener:
    async def start(self):
        conn = await get_db_connection()
        await conn.add_listener("data_changes", self._handle_event)