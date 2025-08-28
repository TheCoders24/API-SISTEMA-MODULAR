import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import WebSocket
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from sqlalchemy import text

from ...database.session import async_session

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "connection_pool_size": 0,
            "timestamp": time.time()
        }
        self.connection_history = []
        self.user_sessions = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.send_stats(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_stats(self, websocket: WebSocket):
        await websocket.send_json({
            "type": "connection_stats",
            "data": self.connection_stats
        })

    async def broadcast(self, message: dict):
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_connections.append(connection)
        
        for connection in disconnected_connections:
            self.disconnect(connection)

    async def update_stats(self):
        try:
            async with async_session() as session:
                # Obtener estadísticas de conexiones a la base de datos
                result = await session.execute(
                    text("""
                    SELECT COUNT(*) FROM pg_stat_activity 
                    WHERE datname = 'sistemainventario'
                    """)
                )
                active_connections = result.scalar()
                
                result = await session.execute(
                    text("""
                    SELECT COUNT(*) FROM pg_stat_activity 
                    WHERE datname = 'sistemainventario' AND state = 'idle'
                    """)
                )
                idle_connections = result.scalar()
                
                result = await session.execute(
                    text("SHOW max_connections")
                )
                max_connections = result.scalar()

                # Obtener usuarios conectados al sistema
                await self.update_user_sessions(session)

            self.connection_stats = {
                "total_connections": active_connections,
                "active_connections": active_connections - idle_connections,
                "idle_connections": idle_connections,
                "connection_pool_size": int(max_connections),
                "timestamp": time.time()
            }
            
            self.connection_history.append({
                **self.connection_stats,
                "timestamp": datetime.now().isoformat()
            })
            
            if len(self.connection_history) > 1000:
                self.connection_history = self.connection_history[-1000:]
            
            await self.broadcast({
                "type": "connection_stats",
                "data": self.connection_stats
            })
            
            return self.connection_stats
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return None

    async def update_user_sessions(self, session):
        """Actualizar la lista de usuarios conectados al sistema"""
        try:
            # Verificar si existe la tabla user_sessions
            result = await session.execute(
                text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_sessions'
                )
                """)
            )
            table_exists = result.scalar()
            
            if not table_exists:
                self.user_sessions = []
                return
            
            # Obtener usuarios activos - CONSULTA CORRECTA para tu estructura
            result = await session.execute(
                text("""
                SELECT 
                    us.id,
                    us.user_id,
                    u.nombre,
                    u.email,
                    us.login_time,
                    us.last_activity,
                    us.ip_address,
                    us.user_agent,
                    us.is_active,
                    EXTRACT(EPOCH FROM (NOW() - us.last_activity)) as inactive_seconds,
                    NOW() - us.login_time as session_duration
                FROM user_sessions us
                LEFT JOIN usuarios u ON us.user_id = u.id
                WHERE us.is_active = true
                ORDER BY us.last_activity DESC
                """)
            )
            
            self.user_sessions = []
            for row in result.mappings():
                session_data = dict(row)
                # Convertir tipos de fecha para JSON
                if session_data.get('login_time'):
                    session_data['login_time'] = session_data['login_time'].isoformat()
                if session_data.get('last_activity'):
                    session_data['last_activity'] = session_data['last_activity'].isoformat()
                self.user_sessions.append(session_data)
                
        except Exception as e:
            print(f"Error actualizando sesiones de usuario: {e}")
            self.user_sessions = []

    def get_connection_trends(self, hours=24):
        now = datetime.now()
        cutoff = now - timedelta(hours=hours)
        
        recent_data = [
            data for data in self.connection_history 
            if datetime.fromisoformat(data["timestamp"]) >= cutoff
        ]
        
        if not recent_data:
            return None
            
        df = pd.DataFrame(recent_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        
        hourly = df.resample("1H").mean()
        
        return {
            "current": self.connection_stats,
            "hourly_avg": hourly.to_dict(),
            "peak_connections": {
                "max_active": df["active_connections"].max(),
                "max_total": df["total_connections"].max(),
                "time_of_peak": df["total_connections"].idxmax().isoformat()
            }
        }
    
    def generate_connection_graph(self, hours=24):
        trends = self.get_connection_trends(hours)
        if not trends:
            return None
            
        df = pd.DataFrame(trends["hourly_avg"])
        
        plt.figure(figsize=(10, 6))
        plt.plot(df.index, df["active_connections"], label="Conexiones Activas", marker='o')
        plt.plot(df.index, df["total_connections"], label="Conexiones Totales", marker='s')
        plt.xlabel("Hora")
        plt.ylabel("Número de Conexiones")
        plt.title(f"Tendencias de Conexiones en las últimas {hours} horas")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{img_str}"

    def get_active_users(self):
        """Obtener usuarios activos en el sistema"""
        return {
            "active_users": self.user_sessions,
            "total_active": len(self.user_sessions),
            "timestamp": datetime.now().isoformat()
        }

    def get_user_activity_stats(self, hours: int = 24):
        """Obtener estadísticas de actividad de usuarios"""
        try:
            if not self.user_sessions:
                return {
                    "unique_users": 0,
                    "total_sessions": 0,
                    "average_session_duration": "00:00:00",
                    "most_recent_activity": None
                }
            
            # Calcular estadísticas básicas
            unique_users = len(set(user['user_id'] for user in self.user_sessions if user['user_id']))
            total_sessions = len(self.user_sessions)
            
            # Calcular duración promedio de sesión
            now = datetime.now()
            total_duration = 0
            for user in self.user_sessions:
                if user.get('login_time'):
                    login_time = datetime.fromisoformat(user['login_time'].replace('Z', '+00:00'))
                    duration = (now - login_time).total_seconds()
                    total_duration += duration
            
            avg_duration_seconds = total_duration / total_sessions if total_sessions > 0 else 0
            hours = int(avg_duration_seconds // 3600)
            minutes = int((avg_duration_seconds % 3600) // 60)
            seconds = int(avg_duration_seconds % 60)
            avg_duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Encontrar actividad más reciente
            most_recent = max(
                (user['last_activity'] for user in self.user_sessions if user.get('last_activity')),
                default=None
            )
            
            return {
                "unique_users": unique_users,
                "total_sessions": total_sessions,
                "average_session_duration": avg_duration,
                "most_recent_activity": most_recent,
                "time_period_hours": hours
            }
            
        except Exception as e:
            print(f"Error calculando estadísticas de usuario: {e}")
            return {
                "unique_users": 0,
                "total_sessions": 0,
                "average_session_duration": "00:00:00",
                "most_recent_activity": None,
                "time_period_hours": hours
            }

# Crear instancia global del manager
manager = ConnectionManager()

# Tarea en segundo plano para actualizar estadísticas
async def stats_background_task():
    while True:
        await manager.update_stats()
        await asyncio.sleep(3)