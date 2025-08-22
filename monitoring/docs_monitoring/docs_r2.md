# **Sistema de Monitoreo para WebSockets - Implementación Completa**

Basado en la explicación detallada, aquí tienes la implementación completa del sistema de monitoreo para WebSockets:

## **1. Estructura del Proyecto**

```
websocket-monitoring-system/
├── main.py
├── monitor.py
├── manager.py
├── alerts.py
├── dashboard/
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   └── App.tsx
│   │   └── package.json
│   └── backend/
│       └── api.py
├── requirements.txt
└── README.md
```

## **2. Implementación del Monitor (monitor.py)**

```python
import asyncio
import json
import time
import psutil
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

@dataclass
class ConnectionInfo:
    id: str
    channel: str
    user_id: Optional[str]
    connected_at: float
    disconnected_at: Optional[float] = None
    messages_sent: int = 0
    messages_received: int = 0
    last_activity: float = None

class WebSocketMonitor:
    def __init__(self):
        self.connections: Dict[str, ConnectionInfo] = {}
        self.channel_connections = defaultdict(list)
        self.metrics = {
            'total_connections': 0,
            'current_connections': 0,
            'connections_per_channel': defaultdict(int),
            'messages_sent': 0,
            'messages_received': 0,
            'connection_durations': [],
            'errors': defaultdict(int),
            'active_since': time.time()
        }
        
        # Historial de métricas para tendencias
        self.history = {
            'connections': [],
            'messages': [],
            'system_metrics': []
        }
        
        # Iniciar tareas de fondo
        self._background_tasks = set()
        
    async def start(self):
        """Iniciar tareas de monitoreo en segundo plano"""
        # Tarea para recolectar métricas del sistema
        task = asyncio.create_task(self._collect_system_metrics())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        
        # Tarea para mantener el historial
        task = asyncio.create_task(self._update_history())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
    
    async def track_connection(self, websocket, channel: str, user_id: str = None):
        """Registrar una nueva conexión"""
        connection_id = f"{channel}_{user_id}_{int(time.time() * 1000)}"
        conn_info = ConnectionInfo(
            id=connection_id,
            channel=channel,
            user_id=user_id,
            connected_at=time.time(),
            last_activity=time.time()
        )
        
        self.connections[connection_id] = conn_info
        self.channel_connections[channel].append(connection_id)
        
        # Actualizar métricas
        self.metrics['total_connections'] += 1
        self.metrics['current_connections'] += 1
        self.metrics['connections_per_channel'][channel] += 1
        
        return connection_id
    
    async def track_disconnection(self, connection_id: str):
        """Registrar una desconexión"""
        if connection_id in self.connections:
            conn_info = self.connections[connection_id]
            conn_info.disconnected_at = time.time()
            
            # Calcular duración
            duration = conn_info.disconnected_at - conn_info.connected_at
            self.metrics['connection_durations'].append(duration)
            
            # Actualizar métricas
            self.metrics['current_connections'] -= 1
            self.metrics['connections_per_channel'][conn_info.channel] -= 1
            
            # Limpiar de conexiones por canal
            if connection_id in self.channel_connections[conn_info.channel]:
                self.channel_connections[conn_info.channel].remove(connection_id)
    
    async def track_message_sent(self, connection_id: str):
        """Registrar mensaje enviado"""
        if connection_id in self.connections:
            self.connections[connection_id].messages_sent += 1
            self.connections[connection_id].last_activity = time.time()
            self.metrics['messages_sent'] += 1
    
    async def track_message_received(self, connection_id: str):
        """Registrar mensaje recibido"""
        if connection_id in self.connections:
            self.connections[connection_id].messages_received += 1
            self.connections[connection_id].last_activity = time.time()
            self.metrics['messages_received'] += 1
    
    async def track_error(self, error_type: str, details: str = ""):
        """Registrar un error"""
        self.metrics['errors'][error_type] += 1
        # Aquí se podría integrar con el sistema de alertas
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas actuales"""
        # Calcular promedios
        avg_duration = 0
        if self.metrics['connection_durations']:
            avg_duration = sum(self.metrics['connection_durations']) / len(self.metrics['connection_durations'])
        
        # Obtener métricas del sistema
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        
        return {
            **self.metrics,
            'avg_connection_duration': avg_duration,
            'channels_active': len(self.channel_connections),
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'uptime': time.time() - self.metrics['active_since'],
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_channel_metrics(self, channel: str) -> Optional[Dict[str, Any]]:
        """Obtener métricas específicas de un canal"""
        if channel not in self.channel_connections:
            return None
        
        connections = [self.connections[conn_id] for conn_id in self.channel_connections[channel] 
                      if conn_id in self.connections]
        
        messages_sent = sum(conn.messages_sent for conn in connections)
        messages_received = sum(conn.messages_received for conn in connections)
        
        return {
            'channel': channel,
            'current_connections': len(connections),
            'messages_sent': messages_sent,
            'messages_received': messages_received,
            'connections': [asdict(conn) for conn in connections]
        }
    
    async def _collect_system_metrics(self):
        """Recolectar métricas del sistema en segundo plano"""
        while True:
            try:
                cpu_usage = psutil.cpu_percent()
                memory_usage = psutil.virtual_memory().percent
                disk_usage = psutil.disk_usage('/').percent
                
                # Aquí se podría enviar a un sistema de almacenamiento de series temporales
                # como Prometheus o InfluxDB
                
                await asyncio.sleep(10)  # Cada 10 segundos
            except Exception as e:
                await self.track_error("system_metrics_error", str(e))
                await asyncio.sleep(30)  # Esperar más en caso de error
    
    async def _update_history(self):
        """Actualizar historial de métricas"""
        while True:
            try:
                metrics = await self.get_metrics()
                timestamp = datetime.now().isoformat()
                
                # Mantener solo las últimas 1000 entradas por tipo
                for key in ['connections', 'messages', 'system_metrics']:
                    if len(self.history[key]) >= 1000:
                        self.history[key].pop(0)
                
                self.history['connections'].append({
                    'timestamp': timestamp,
                    'current': metrics['current_connections'],
                    'total': metrics['total_connections']
                })
                
                self.history['messages'].append({
                    'timestamp': timestamp,
                    'sent': metrics['messages_sent'],
                    'received': metrics['messages_received']
                })
                
                self.history['system_metrics'].append({
                    'timestamp': timestamp,
                    'cpu': metrics['cpu_usage'],
                    'memory': metrics['memory_usage']
                })
                
                await asyncio.sleep(60)  # Actualizar cada minuto
            except Exception as e:
                await self.track_error("history_update_error", str(e))
                await asyncio.sleep(120)

# Instancia global del monitor
websocket_monitor = WebSocketMonitor()
```

## **3. Implementación del Manager (manager.py)**

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import asyncio
from .monitor import websocket_monitor

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.connection_info: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket, channel: str, user_id: str = None):
        """Manejar nueva conexión"""
        await websocket.accept()
        
        # Registrar en el monitor
        connection_id = await websocket_monitor.track_connection(websocket, channel, user_id)
        
        # Almacenar información de conexión
        self.active_connections[channel].append(websocket)
        self.connection_info[websocket] = {
            'id': connection_id,
            'channel': channel,
            'user_id': user_id
        }
        
        return connection_id
    
    async def disconnect(self, websocket: WebSocket):
        """Manejar desconexión"""
        if websocket in self.connection_info:
            info = self.connection_info[websocket]
            connection_id = info['id']
            channel = info['channel']
            
            # Remover de conexiones activas
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
            
            # Registrar en el monitor
            await websocket_monitor.track_disconnection(connection_id)
            
            # Limpiar información
            del self.connection_info[websocket]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Enviar mensaje a un websocket específico"""
        if websocket in self.connection_info:
            connection_id = self.connection_info[websocket]['id']
            await websocket.send_text(message)
            await websocket_monitor.track_message_sent(connection_id)
    
    async def broadcast(self, message: str, channel: str):
        """Transmitir mensaje a todos en un canal"""
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_text(message)
                    connection_id = self.connection_info[connection]['id']
                    await websocket_monitor.track_message_sent(connection_id)
                except Exception as e:
                    # Manejar conexiones muertas
                    await self.disconnect(connection)
                    await websocket_monitor.track_error("broadcast_error", f"Failed to send to {connection_id}: {str(e)}")
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """Manejar mensaje recibido"""
        if websocket in self.connection_info:
            connection_id = self.connection_info[websocket]['id']
            await websocket_monitor.track_message_received(connection_id)
            
            try:
                # Procesar mensaje (aquí puedes añadir tu lógica de negocio)
                message_data = json.loads(message)
                
                # Ejemplo: reenviar mensaje a todos en el mismo canal
                if message_data.get('type') == 'broadcast':
                    channel = self.connection_info[websocket]['channel']
                    await self.broadcast(message, channel)
                
            except json.JSONDecodeError:
                await websocket_monitor.track_error("invalid_message", f"Invalid JSON: {message}")
            except Exception as e:
                await websocket_monitor.track_error("message_processing", f"Error processing message: {str(e)}")

# Instancia global del manager
websocket_manager = WebSocketManager()
```

## **4. Implementación del Sistema de Alertas (alerts.py)**

```python
import asyncio
import smtplib
from email.mime.text import MIMEText
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime

class AlertSystem:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_cooldown = {}  # Para evitar alertas repetitivas
        self.alert_history = []
    
    async def send_alert(self, level: str, message: str, details: Dict[str, Any] = None):
        """Enviar alerta según el nivel de severidad"""
        # Verificar cooldown para evitar spam
        alert_key = f"{level}_{message}"
        current_time = datetime.now().timestamp()
        
        if alert_key in self.alert_cooldown:
            if current_time - self.alert_cooldown[alert_key] < self.config.get('cooldown_period', 300):
                return  # En cooldown, no enviar
        
        self.alert_cooldown[alert_key] = current_time
        
        # Construir mensaje de alerta
        full_message = f"[{level.upper()}] {message}\n\n"
        if details:
            for key, value in details.items():
                full_message += f"{key}: {value}\n"
        
        full_message += f"\nTimestamp: {datetime.now().isoformat()}"
        
        # Enviar por los canales configurados
        channels = self.config.get('channels', {})
        
        if 'email' in channels and level in channels['email'].get('levels', ['critical']):
            await self._send_email(full_message, channels['email'])
        
        if 'slack' in channels and level in channels['slack'].get('levels', ['critical', 'warning']):
            await self._send_slack(full_message, channels['slack'])
        
        if 'sms' in channels and level in channels['sms'].get('levels', ['critical']):
            await self._send_sms(full_message, channels['sms'])
        
        # Guardar en historial
        self.alert_history.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'details': details
        })
        
        # Limitar historial a 1000 entradas
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
    
    async def check_thresholds(self, metrics: Dict[str, Any]):
        """Verificar métricas contra umbrales configurados"""
        thresholds = self.config.get('thresholds', {})
        
        # Verificar uso de CPU
        if 'high_cpu' in thresholds and metrics.get('cpu_usage', 0) > thresholds['high_cpu']:
            await self.send_alert(
                'warning' if metrics['cpu_usage'] < 90 else 'critical',
                f"High CPU usage detected",
                {'current': f"{metrics['cpu_usage']}%", 'threshold': f"{thresholds['high_cpu']}%"}
            )
        
        # Verificar uso de memoria
        if 'high_memory' in thresholds and metrics.get('memory_usage', 0) > thresholds['high_memory']:
            await self.send_alert(
                'warning' if metrics['memory_usage'] < 90 else 'critical',
                f"High memory usage detected",
                {'current': f"{metrics['memory_usage']}%", 'threshold': f"{thresholds['high_memory']}%"}
            )
        
        # Verificar número de conexiones
        if 'max_connections' in thresholds and metrics.get('current_connections', 0) > thresholds['max_connections']:
            await self.send_alert(
                'warning',
                f"High number of connections",
                {'current': metrics['current_connections'], 'threshold': thresholds['max_connections']}
            )
        
        # Verificar errores
        error_threshold = thresholds.get('error_threshold', 5)
        total_errors = sum(metrics.get('errors', {}).values())
        if total_errors > error_threshold:
            await self.send_alert(
                'warning' if total_errors < 10 else 'critical',
                f"High error rate detected",
                {'current': total_errors, 'threshold': error_threshold, 'errors': dict(metrics.get('errors', {}))}
            )
    
    async def _send_email(self, message: str, config: Dict[str, Any]):
        """Enviar alerta por email"""
        try:
            msg = MIMEText(message)
            msg['Subject'] = config.get('subject', 'WebSocket Monitoring Alert')
            msg['From'] = config.get('from_email', 'alerts@websocket-monitor.com')
            msg['To'] = ', '.join(config.get('recipients', []))
            
            with smtplib.SMTP(config.get('smtp_server', 'localhost'), config.get('smtp_port', 25)) as server:
                if config.get('use_tls', False):
                    server.starttls()
                if config.get('smtp_user') and config.get('smtp_password'):
                    server.login(config['smtp_user'], config['smtp_password'])
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {str(e)}")
    
    async def _send_slack(self, message: str, config: Dict[str, Any]):
        """Enviar alerta a Slack"""
        try:
            webhook_url = config.get('webhook_url')
            if not webhook_url:
                return
            
            payload = {
                'text': message,
                'username': config.get('username', 'WebSocket Monitor'),
                'icon_emoji': config.get('icon_emoji', ':warning:')
            }
            
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                print(f"Failed to send Slack alert: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Failed to send Slack alert: {str(e)}")
    
    async def _send_sms(self, message: str, config: Dict[str, Any]):
        """Enviar alerta por SMS (implementación básica)"""
        # Esta es una implementación básica. En producción, usarías un servicio como Twilio
        print(f"SMS Alert (to {config.get('numbers', ['N/A'])}): {message}")

# Configuración de ejemplo
alert_config = {
    'thresholds': {
        'high_cpu': 80,
        'high_memory': 85,
        'max_connections': 500,
        'error_threshold': 5
    },
    'channels': {
        'email': {
            'levels': ['critical', 'warning'],
            'recipients': ['devops@example.com', 'admin@example.com'],
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'smtp_user': 'alerts@example.com',
            'smtp_password': 'password',
            'use_tls': True
        },
        'slack': {
            'levels': ['critical', 'warning'],
            'webhook_url': 'https://hooks.slack.com/services/...',
            'username': 'WebSocket Alerts',
            'icon_emoji': ':warning:'
        },
        'sms': {
            'levels': ['critical'],
            'numbers': ['+1234567890']
        }
    },
    'cooldown_period': 300  # 5 minutos entre alertas del mismo tipo
}

# Instancia global del sistema de alertas
alert_system = AlertSystem(alert_config)
```

## **5. Implementación del API del Dashboard (dashboard/backend/api.py)**

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict, List
import json
import asyncio
from ...monitor import websocket_monitor
from ...manager import websocket_manager
from ...alerts import alert_system

router = APIRouter()

# Endpoints para obtener métricas
@router.get("/metrics")
async def get_metrics():
    """Obtener métricas actuales del sistema"""
    return await websocket_monitor.get_metrics()

@router.get("/metrics/history")
async def get_metrics_history(metric_type: str = "connections", limit: int = 100):
    """Obtener historial de métricas"""
    if metric_type in websocket_monitor.history:
        return websocket_monitor.history[metric_type][-limit:]
    return {"error": "Invalid metric type"}

@router.get("/metrics/channel/{channel_name}")
async def get_channel_metrics(channel_name: str):
    """Obtener métricas de un canal específico"""
    return await websocket_monitor.get_channel_metrics(channel_name)

@router.get("/connections")
async def get_connections(limit: int = 50):
    """Obtener información de conexiones activas"""
    connections = []
    for conn_id, conn_info in list(websocket_monitor.connections.items())[-limit:]:
        if conn_info.disconnected_at is None:  # Solo conexiones activas
            connections.append(conn_info)
    return connections

@router.get("/alerts")
async def get_alerts(limit: int = 50):
    """Obtener historial de alertas"""
    return alert_system.alert_history[-limit:]

# WebSocket para actualizaciones en tiempo real
@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket para actualizaciones del dashboard en tiempo real"""
    await websocket.accept()
    try:
        # Enviar actualizaciones periódicas
        while True:
            metrics = await websocket_monitor.get_metrics()
            await websocket.send_json({
                "type": "metrics_update",
                "data": metrics
            })
            await asyncio.sleep(5)  # Actualizar cada 5 segundos
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Dashboard WebSocket error: {str(e)}")
```

## **6. Aplicación Principal (main.py)**

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import json
from typing import Dict

from monitor import websocket_monitor
from manager import websocket_manager
from alerts import alert_system
from dashboard.backend.api import router as dashboard_router

app = FastAPI(title="WebSocket Monitoring System")

# Montar el dashboard
app.mount("/static", StaticFiles(directory="dashboard/frontend/dist"), name="static")
templates = Jinja2Templates(directory="dashboard/frontend/dist")

# Incluir rutas del dashboard
app.include_router(dashboard_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Inicializar el sistema al arrancar"""
    await websocket_monitor.start()
    print("WebSocket Monitoring System started")

@app.get("/")
async def get_dashboard(request: Request):
    """Servir el dashboard principal"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{channel}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, channel: str, user_id: str):
    """Endpoint principal de WebSocket"""
    connection_id = await websocket_manager.connect(websocket, channel, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        await websocket_monitor.track_error("websocket_error", f"Connection {connection_id}: {str(e)}")
        await websocket_manager.disconnect(websocket)

# Tarea en segundo plano para verificar alertas
@app.on_event("startup")
async def start_alert_checking():
    """Iniciar verificación periódica de alertas"""
    async def check_alerts():
        while True:
            try:
                metrics = await websocket_monitor.get_metrics()
                await alert_system.check_thresholds(metrics)
            except Exception as e:
                print(f"Alert checking error: {str(e)}")
            await asyncio.sleep(30)  # Verificar cada 30 segundos
    
    asyncio.create_task(check_alerts())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## **7. Frontend del Dashboard (dashboard/frontend/src/App.tsx)**

```tsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

interface Metric {
  timestamp: string;
  current_connections: number;
  messages_sent: number;
  messages_received: number;
  cpu_usage: number;
  memory_usage: number;
}

interface Alert {
  timestamp: string;
  level: string;
  message: string;
  details: any;
}

function App() {
  const [metrics, setMetrics] = useState<Metric | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Conectar al WebSocket para actualizaciones en tiempo real
    const websocket = new WebSocket(`ws://${window.location.host}/ws/dashboard`);
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'metrics_update') {
        setMetrics(data.data);
      }
    };
    
    setWs(websocket);

    // Cargar datos iniciales
    fetchMetrics();
    fetchHistory();
    fetchAlerts();

    return () => {
      websocket.close();
    };
  }, []);

  const fetchMetrics = async () => {
    const response = await fetch('/api/metrics');
    const data = await response.json();
    setMetrics(data);
  };

  const fetchHistory = async () => {
    const response = await fetch('/api/metrics/history?metric_type=connections&limit=100');
    const data = await response.json();
    setHistory(data);
  };

  const fetchAlerts = async () => {
    const response = await fetch('/api/alerts?limit=10');
    const data = await response.json();
    setAlerts(data);
  };

  if (!metrics) {
    return <div className="loading">Cargando métricas...</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Sistema de Monitoreo WebSocket</h1>
        <div className="status-indicators">
          <div className={`status-indicator ${metrics.cpu_usage > 80 ? 'warning' : ''}`}>
            CPU: {metrics.cpu_usage}%
          </div>
          <div className={`status-indicator ${metrics.memory_usage > 85 ? 'warning' : ''}`}>
            Memoria: {metrics.memory_usage}%
          </div>
          <div className="status-indicator">
            Conexiones: {metrics.current_connections}
          </div>
        </div>
      </header>

      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Conexiones Activas</h3>
          <span className="metric-value">{metrics.current_connections}</span>
        </div>
        
        <div className="metric-card">
          <h3>Mensajes Enviados</h3>
          <span className="metric-value">{metrics.messages_sent}</span>
        </div>
        
        <div className="metric-card">
          <h3>Mensajes Recibidos</h3>
          <span className="metric-value">{metrics.messages_received}</span>
        </div>
        
        <div className="metric-card">
          <h3>Uso de CPU</h3>
          <span className={`metric-value ${metrics.cpu_usage > 80 ? 'warning' : ''}`}>
            {metrics.cpu_usage}%
          </span>
        </div>
      </div>

      <div className="charts-section">
        <div className="chart-card">
          <h3>Conexiones en el Tiempo</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="current" stroke="#8884d8" name="Conexiones" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="alerts-section">
        <h2>Alertas Recientes</h2>
        <div className="alerts-list">
          {alerts.map((alert, index) => (
            <div key={index} className={`alert-item ${alert.level}`}>
              <div className="alert-time">{new Date(alert.timestamp).toLocaleTimeString()}</div>
              <div className="alert-message">{alert.message}</div>
              <div className="alert-details">{JSON.stringify(alert.details)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
```

## **8. Requirements.txt**

```txt
fastapi==0.68.0
uvicorn==0.15.0
websockets==10.1
psutil==5.8.0
aiohttp==3.8.1
requests==2.26.0
python-multipart==0.0.5
Jinja2==3.0.1
```

## **9. Instrucciones de Uso**

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

3. **Acceder al dashboard:**
   Abrir http://localhost:8000 en el navegador

4. **Conectarse al WebSocket:**
   ```javascript
   // Ejemplo de cliente WebSocket
   const ws = new WebSocket('ws://localhost:8000/ws/canal_ventas/usuario_123');
   
   ws.onmessage = (event) => {
     console.log('Mensaje recibido:', event.data);
   };
   
   ws.send(JSON.stringify({type: 'message', content: 'Hola mundo'}));
   ```

## **10. Características Adicionales Implementadas**

1. **Métricas del sistema** (CPU, memoria) en tiempo real
2. **Historial de métricas** para análisis de tendencias
3. **Sistema de alertas** configurable con múltiples canales
4. **Dashboard interactivo** con gráficos en tiempo real
5. **Manejo robusto de errores** y desconexiones
6. **Métricas por canal** para análisis granular
7. **API REST** para integración con otros sistemas

Este sistema proporciona una solución completa para monitorear WebSockets en producción, con todas las características necesarias para mantener un sistema saludable y responder rápidamente a problemas.