from collections import defaultdict
from fastapi import WebSocket
from typing import Dict, List, Set
import asyncio
import logging
from datetime import datetime
import json
from ..database.postgres_manager import postgres_manager

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.connection_metadata: Dict[WebSocket, dict] = {}
        self.channel_subscriptions: Dict[str, Set[WebSocket]] = defaultdict(set)
    
    async def connect(self, websocket: WebSocket, channel: str, metadata: dict = None):
        """Add connection to channel with metadata and log to PostgreSQL"""
        self.active_connections[channel].append(websocket)
        self.channel_subscriptions[channel].add(websocket)
        
        connection_data = {
            'channel': channel,
            'connected_at': datetime.now(),
            'last_activity': datetime.now(),
            **(metadata or {})
        }
        self.connection_metadata[websocket] = connection_data
        
        # Log connection to PostgreSQL
        try:
            async with postgres_manager.get_connection() as conn:
                await conn.execute('''
                    INSERT INTO connection_metrics 
                    (connection_id, user_id, channel, event_type, success)
                    VALUES ($1, $2, $3, $4, $5)
                ''', str(id(websocket)), metadata.get('user_id') if metadata else None, 
                   channel, 'connect', True)
        except Exception as e:
            logger.error(f"Error logging connection: {e}")
        
        logger.info(f"Client connected to channel: {channel}")
    
    async def disconnect(self, websocket: WebSocket, channel: str = None):
        """Remove connection from channel and log to PostgreSQL"""
        if not channel:
            metadata = self.connection_metadata.get(websocket, {})
            channel = metadata.get('channel')
        
        if channel and channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
            
            if websocket in self.channel_subscriptions[channel]:
                self.channel_subscriptions[channel].remove(websocket)
            
            # Clean empty channels
            if not self.active_connections[channel]:
                del self.active_connections[channel]
                del self.channel_subscriptions[channel]
        
        # Log disconnection to PostgreSQL
        metadata = self.connection_metadata.get(websocket, {})
        try:
            async with postgres_manager.get_connection() as conn:
                duration = (datetime.now() - metadata.get('connected_at', datetime.now())).total_seconds() * 1000
                await conn.execute('''
                    INSERT INTO connection_metrics 
                    (connection_id, user_id, channel, event_type, success, duration_ms)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', str(id(websocket)), metadata.get('user_id'), channel, 'disconnect', True, int(duration))
        except Exception as e:
            logger.error(f"Error logging disconnection: {e}")
        
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
    
    async def broadcast(self, channel: str, message: dict):
        """Send message to all connections in a channel with delivery tracking"""
        if channel not in self.channel_subscriptions:
            return
        
        message_id = f"msg_{datetime.now().timestamp()}_{channel}"
        message_with_id = {
            **message,
            "message_id": message_id,
            "timestamp": datetime.now().isoformat()
        }
        
        disconnected = []
        successful_deliveries = 0
        
        for ws in list(self.channel_subscriptions[channel]):
            try:
                await ws.send_json(message_with_id)
                self.connection_metadata[ws]['last_activity'] = datetime.now()
                successful_deliveries += 1
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.append(ws)
        
        # Log message delivery to PostgreSQL
        try:
            async with postgres_manager.get_connection() as conn:
                await conn.execute('''
                    INSERT INTO message_queue 
                    (message_id, channel, message_type, payload, status, delivered_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', message_id, channel, message.get('type', 'unknown'), 
                   json.dumps(message), 'delivered', datetime.now())
        except Exception as e:
            logger.error(f"Error logging message: {e}")
        
        # Clean up disconnected clients
        for ws in disconnected:
            await self.disconnect(ws, channel)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user across all their connections"""
        user_channel = f"user_{user_id}"
        await self.broadcast(user_channel, message)
    
    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe connection to additional channel"""
        self.channel_subscriptions[channel].add(websocket)
    
    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe connection from channel"""
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(websocket)
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            'total_connections': sum(len(conns) for conns in self.active_connections.values()),
            'total_channels': len(self.active_connections),
            'channels': {chan: len(conns) for chan, conns in self.active_connections.items()}
        }

# Global instance
ws_manager = WebSocketManager()