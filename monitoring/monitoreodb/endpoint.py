from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy import text
import time
from datetime import datetime
from ...database.session import async_session
from .manager import manager

router = APIRouter()

@router.websocket("/ws/connections")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "refresh":
                await manager.update_stats()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        manager.disconnect(websocket)

@router.get("/connection-stats")
async def get_connection_stats():
    stats = await manager.update_stats()
    if stats:
        return stats
    else:
        raise HTTPException(status_code=500, detail="Error al obtener estadísticas")

@router.get("/connection-details")
async def get_connection_details():
    try:
        async with async_session() as session:
            result = await session.execute(
                text("""
                SELECT 
                    pid, 
                    usename, 
                    application_name, 
                    client_addr,
                    state,
                    query_start,
                    query 
                FROM pg_stat_activity 
                WHERE datname = 'sistemainventario'
                """)
            )
            connections = result.mappings().all()
            
            return {
                "connections": connections,
                "count": len(connections),
                "timestamp": time.time()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener detalles: {str(e)}")

@router.get("/connection-analytics")
async def get_connection_analytics(hours: int = 24):
    try:
        trends = manager.get_connection_trends(hours)
        if not trends:
            raise HTTPException(status_code=404, detail="No hay datos suficientes para analytics")
        
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar analytics: {str(e)}")

@router.get("/connection-graph")
async def get_connection_graph(hours: int = 24):
    try:
        graph_data = manager.generate_connection_graph(hours)
        if not graph_data:
            raise HTTPException(status_code=404, detail="No hay datos suficientes para generar gráfico")
        
        return {"graph": graph_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar gráfico: {str(e)}")

@router.get("/db-performance")
async def get_db_performance():
    try:
        async with async_session() as session:
            result = await session.execute(
                text("""
                SELECT 
                    schemaname,
                    relname,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del
                FROM pg_stat_user_tables
                ORDER BY seq_scan DESC
                LIMIT 10
                """)
            )
            table_stats = result.mappings().all()
            
            result = await session.execute(
                text("""
                SELECT 
                    schemaname,
                    relname,
                    indexrelname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
                LIMIT 10
                """)
            )
            index_stats = result.mappings().all()
            
            return {
                "table_stats": table_stats,
                "index_stats": index_stats,
                "timestamp": time.time()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener métricas de rendimiento: {str(e)}")

# NUEVOS ENDPOINTS PARA USUARIOS CONECTADOS
@router.get("/active-users")
async def get_active_users():
    """Obtener lista de usuarios activos en el sistema"""
    try:
        # Forzar actualización de las sesiones de usuario
        async with async_session() as session:
            await manager.update_user_sessions(session)
        
        users_data = manager.get_active_users()
        return users_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios activos: {str(e)}")

@router.get("/user-activity-stats")
async def get_user_activity_stats(hours: int = 24):
    """Obtener estadísticas de actividad de usuarios"""
    try:
        # Forzar actualización primero
        async with async_session() as session:
            await manager.update_user_sessions(session)
        
        stats = manager.get_user_activity_stats(hours)
        return {
            **stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas de usuario: {str(e)}")