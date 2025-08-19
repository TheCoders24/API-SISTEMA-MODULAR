# **FUNCIÓN DE MONITOREO PARA WEBSOCKETS - IMPLEMENTACIÓN COMPLETA**

## **1. SISTEMA DE MONITOREO EN TIEMPO REAL**

### **1.1. Clase de Monitoreo Mejorada**
```python
# monitoring/websocket_monitor.py
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import psutil
import json

class WebSocketMonitor:
    def __init__(self):
        self.connections = defaultdict(list)
        self.metrics = {
            'total_connections': 0,
            'connections_per_channel': defaultdict(int),
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        self.connection_history = []
        self.performance_data = []
        
    async def track_connection(self, websocket, channel: str, user_id: str = None):
        """Registrar nueva conexión con metadata"""
        connection_data = {
            'id': id(websocket),
            'channel': channel,
            'user_id': user_id,
            'connected_at': datetime.now(),
            'remote_addr': getattr(websocket, 'client_host', 'unknown'),
            'user_agent': getattr(websocket, 'headers', {}).get('user-agent', 'unknown')
        }
        
        self.connections[channel].append(connection_data)
        self.metrics['total_connections'] += 1
        self.metrics['connections_per_channel'][channel] += 1
        self.connection_history.append(connection_data)
        
        # Limitar historial a las últimas 1000 conexiones
        if len(self.connection_history) > 1000:
            self.connection_history.pop(0)
    
    async def track_disconnection(self, websocket, channel: str):
        """Registrar desconexión"""
        for conn in self.connections[channel]:
            if conn['id'] == id(websocket):
                conn['disconnected_at'] = datetime.now()
                conn['duration'] = (conn['disconnected_at'] - conn['connected_at']).total_seconds()
                break
        
        self.metrics['connections_per_channel'][channel] -= 1
        if self.metrics['connections_per_channel'][channel] <= 0:
            del self.metrics['connections_per_channel'][channel]
    
    async def track_message(self, direction: str, size: int, channel: str = None):
        """Registrar mensajes (sent/received)"""
        if direction == 'sent':
            self.metrics['messages_sent'] += 1
        else:
            self.metrics['messages_received'] += 1
        
        message_metric = {
            'timestamp': datetime.now(),
            'direction': direction,
            'size': size,
            'channel': channel
        }
        self.performance_data.append(message_metric)
    
    async def track_error(self, error_type: str, details: str = None):
        """Registrar errores"""
        self.metrics['errors'] += 1
        error_data = {
            'timestamp': datetime.now(),
            'type': error_type,
            'details': details
        }
    
    async def get_real_time_metrics(self):
        """Obtener métricas en tiempo real"""
        return {
            'current_connections': self.metrics['total_connections'],
            'connections_by_channel': dict(self.metrics['connections_per_channel']),
            'messages_sent': self.metrics['messages_sent'],
            'messages_received': self.metrics['messages_received'],
            'errors': self.metrics['errors'],
            'uptime': (datetime.now() - self.metrics['start_time']).total_seconds(),
            'system_metrics': await self._get_system_metrics()
        }
    
    async def _get_system_metrics(self):
        """Métricas del sistema"""
        return {
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(),
            'active_threads': threading.active_count(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_connection_stats(self, hours: int = 24):
        """Estadísticas de conexiones por período"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_connections = [
            conn for conn in self.connection_history 
            if conn['connected_at'] >= cutoff_time
        ]
        
        return {
            'total_connections': len(recent_connections),
            'avg_duration': sum(conn.get('duration', 0) for conn in recent_connections) / max(len(recent_connections), 1),
            'unique_channels': len(set(conn['channel'] for conn in recent_connections)),
            'peak_connections': max(self.metrics['connections_per_channel'].values(), default=0)
        }

# Instancia global del monitor
websocket_monitor = WebSocketMonitor()
```

### **1.2. Integración con WebSocket Manager**
```python
# infrastructure/websocket/manager.py
from monitoring.websocket_monitor import websocket_monitor

class WebSocketManager:
    def __init__(self):
        self.active_connections = defaultdict(list)
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str, user_id: str = None):
        async with self.lock:
            self.active_connections[channel].append(websocket)
            await websocket_monitor.track_connection(websocket, channel, user_id)
            logger.info(f"New connection to channel '{channel}' - Total: {len(self.active_connections[channel])}")

    async def disconnect(self, websocket: WebSocket, channel: str):
        async with self.lock:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
                await websocket_monitor.track_disconnection(websocket, channel)
                logger.info(f"Disconnected from channel '{channel}' - Remaining: {len(self.active_connections[channel])}")

    async def broadcast(self, message: str, channel: str):
        async with self.lock:
            message_size = len(message.encode('utf-8'))
            dead_connections = []
            
            for connection in self.active_connections.get(channel, []):
                try:
                    await connection.send_text(message)
                    await websocket_monitor.track_message('sent', message_size, channel)
                except Exception as e:
                    dead_connections.append(connection)
                    await websocket_monitor.track_error('send_error', str(e))
            
            for conn in dead_connections:
                await self.disconnect(conn, channel)
```

### **1.3. Endpoints de Monitoreo**
```python
# presentation/api/monitoring_routes.py
from fastapi import APIRouter, Depends
from monitoring.websocket_monitor import websocket_monitor

monitoring_router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@monitoring_router.get("/websocket/metrics")
async def get_websocket_metrics():
    """Obtener métricas en tiempo real de WebSockets"""
    return await websocket_monitor.get_real_time_metrics()

@monitoring_router.get("/websocket/connections")
async def get_active_connections():
    """Listar conexiones activas"""
    return {
        'active_connections': websocket_monitor.connections,
        'total_active': websocket_monitor.metrics['total_connections']
    }

@monitoring_router.get("/websocket/stats/{hours}")
async def get_connection_stats(hours: int = 24):
    """Estadísticas de conexiones históricas"""
    return await websocket_monitor.get_connection_stats(hours)

@monitoring_router.get("/websocket/health")
async def health_check():
    """Health check del sistema WebSocket"""
    metrics = await websocket_monitor.get_real_time_metrics()
    return {
        'status': 'healthy' if metrics['current_connections'] >= 0 else 'unhealthy',
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics
    }
```

## **2. DASHBOARD DE MONITOREO EN TIEMPO REAL**

### **2.1. Componente React para el Dashboard**
```tsx
// frontend/components/WebSocketDashboard.tsx
import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

const WebSocketDashboard: React.FC = () => {
    const [metrics, setMetrics] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);

    // Conectar al canal de métricas
    useWebSocket('monitoring_metrics', (data) => {
        setMetrics(data);
        setHistory(prev => [data, ...prev].slice(0, 100));
    });

    useEffect(() => {
        // Polling cada 5 segundos para métricas detalladas
        const interval = setInterval(async () => {
            const response = await fetch('/api/monitoring/websocket/metrics');
            const data = await response.json();
            setMetrics(data);
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    if (!metrics) return <div>Cargando métricas...</div>;

    return (
        <div className="websocket-dashboard">
            <h2>WebSocket Monitoring Dashboard</h2>
            
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
                    <h3>Errores</h3>
                    <span className="metric-value error">{metrics.errors}</span>
                </div>
            </div>

            <div className="charts-section">
                <ConnectionChart history={history} />
                <SystemMetrics metrics={metrics.system_metrics} />
            </div>
        </div>
    );
};
```

### **2.2. Gráficos en Tiempo Real**


# **FUNCIÓN DE MONITOREO PARA WEBSOCKETS - CONTINUACIÓN**

## **2.3. Gráficos en Tiempo Real (Continuación)**

```tsx
// frontend/components/ConnectionChart.tsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const ConnectionChart: React.FC<{ history: any[] }> = ({ history }) => {
    const data = history.reverse().map((item, index) => ({
        time: new Date(item.timestamp).toLocaleTimeString(),
        connections: item.current_connections,
        messages: item.messages_sent + item.messages_received,
        cpu: item.system_metrics?.cpu_usage || 0,
        memory: item.system_metrics?.memory_usage || 0
    }));

    return (
        <div className="chart-container">
            <h4>Conexiones y Mensajes en Tiempo Real</h4>
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="connections" 
                        stroke="#8884d8" 
                        strokeWidth={2}
                    />
                    <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="messages" 
                        stroke="#82ca9d" 
                        strokeWidth={2}
                    />
                    <Line 
                        yAxisId="right"
                        type="monotone" 
                        dataKey="cpu" 
                        stroke="#ff7300" 
                        strokeWidth={1}
                    />
                    <Line 
                        yAxisId="right"
                        type="monotone" 
                        dataKey="memory" 
                        stroke="#ff0000" 
                        strokeWidth={1}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
```

## **2.4. Componente de Métricas del Sistema**

```tsx
// frontend/components/SystemMetrics.tsx
import React from 'react';
import { BarChart, Bar, Cell, ResponsiveContainer } from 'recharts';

const SystemMetrics: React.FC<{ metrics: any }> = ({ metrics }) => {
    const systemData = [
        { name: 'CPU', value: metrics?.cpu_usage || 0, max: 100 },
        { name: 'Memoria', value: metrics?.memory_usage || 0, max: 100 },
        { name: 'Conexiones', value: metrics?.current_connections || 0, max: 1000 }
    ];

    const getColor = (value: number, max: number) => {
        const percentage = (value / max) * 100;
        if (percentage > 90) return '#ff4d4f';
        if (percentage > 70) return '#faad14';
        return '#52c41a';
    };

    return (
        <div className="system-metrics">
            <h4>Métricas del Sistema</h4>
            <ResponsiveContainer width="100%" height={200}>
                <BarChart data={systemData}>
                    <Bar dataKey="value">
                        {systemData.map((entry, index) => (
                            <Cell 
                                key={`cell-${index}`} 
                                fill={getColor(entry.value, entry.max)} 
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
            <div className="metrics-labels">
                {systemData.map((metric, index) => (
                    <div key={index} className="metric-label">
                        <span>{metric.name}: </span>
                        <strong>{metric.value}</strong>
                        {metric.max && <small> / {metric.max}</small>}
                    </div>
                ))}
            </div>
        </div>
    );
};
```

## **3. ALERTAS Y NOTIFICACIONES AUTOMÁTICAS**

### **3.1. Sistema de Alertas en Backend**

```python
# monitoring/alerts.py
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from slack_sdk import WebClient

class AlertSystem:
    def __init__(self):
        self.alerts_sent = {}
        self.alert_cooldown = timedelta(minutes=5)  # Prevenir spam de alertas
    
    async def check_thresholds(self, metrics: dict):
        """Verificar umbrales y enviar alertas si es necesario"""
        current_time = datetime.now()
        
        # Umbrales configurables
        thresholds = {
            'high_cpu': (80, 'CPU usage above 80%'),
            'high_memory': (85, 'Memory usage above 85%'),
            'high_connections': (500, 'Connection count above 500'),
            'error_rate': (10, 'High error rate detected')
        }
        
        alerts_to_send = []
        
        # Verificar cada umbral
        if metrics['system_metrics']['cpu_usage'] > thresholds['high_cpu'][0]:
            alerts_to_send.append(thresholds['high_cpu'][1])
        
        if metrics['system_metrics']['memory_usage'] > thresholds['high_memory'][0]:
            alerts_to_send.append(thresholds['high_memory'][1])
        
        if metrics['current_connections'] > thresholds['high_connections'][0]:
            alerts_to_send.append(thresholds['high_connections'][1])
        
        if metrics['errors'] > thresholds['error_rate'][0]:
            alerts_to_send.append(thresholds['error_rate'][1])
        
        # Enviar alertas si es necesario
        for alert in alerts_to_send:
            await self.send_alert(alert, metrics, current_time)
    
    async def send_alert(self, alert_message: str, metrics: dict, timestamp: datetime):
        """Enviar alerta por múltiples canales"""
        alert_key = f"{alert_message}_{timestamp.hour}"
        
        # Verificar cooldown
        if alert_key in self.alerts_sent:
            last_sent = self.alerts_sent[alert_key]
            if timestamp - last_sent < self.alert_cooldown:
                return  # Esperar cooldown
        
        # Formatear mensaje de alerta
        message = f"""
        🚨 ALERTA DEL SISTEMA WEBSOCKET 🚨
        
        Mensaje: {alert_message}
        Timestamp: {timestamp.isoformat()}
        
        Métricas Actuales:
        - Conexiones: {metrics['current_connections']}
        - CPU: {metrics['system_metrics']['cpu_usage']}%
        - Memoria: {metrics['system_metrics']['memory_usage']}%
        - Errores: {metrics['errors']}
        - Uptime: {metrics['uptime']} segundos
        """
        
        try:
            # Enviar por email
            await self.send_email_alert(message)
            
            # Enviar por Slack
            await self.send_slack_alert(message)
            
            # Enviar por SMS (Twilio)
            await self.send_sms_alert(message)
            
            # Registrar alerta enviada
            self.alerts_sent[alert_key] = timestamp
            logger.warning(f"Alerta enviada: {alert_message}")
            
        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")
    
    async def send_email_alert(self, message: str):
        """Enviar alerta por email"""
        msg = MIMEText(message)
        msg['Subject'] = '🚨 Alerta del Sistema WebSocket'
        msg['From'] = 'alerts@yourcompany.com'
        msg['To'] = 'devops@yourcompany.com'
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('your_email@gmail.com', 'your_password')
            server.send_message(msg)
    
    async def send_slack_alert(self, message: str):
        """Enviar alerta por Slack"""
        client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        response = client.chat_postMessage(
            channel='#system-alerts',
            text=message,
            icon_emoji=':warning:'
        )
    
    async def send_sms_alert(self, message: str):
        """Enviar alerta por SMS"""
        from twilio.rest import Client
        
        client = Client(os.getenv('TWILIO_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
        client.messages.create(
            body=message[:160],  # Limitar a 160 caracteres
            from_=os.getenv('TWILIO_PHONE_NUMBER'),
            to=os.getenv('ON_CALL_PHONE_NUMBER')
        )

# Instancia global del sistema de alertas
alert_system = AlertSystem()
```

### **3.2. Integración con el Monitoreo**

```python
# monitoring/websocket_monitor.py
from .alerts import alert_system

class WebSocketMonitor:
    # ... [código anterior] ...
    
    async def get_real_time_metrics(self):
        """Obtener métricas y verificar alertas"""
        metrics = {
            'current_connections': self.metrics['total_connections'],
            'connections_by_channel': dict(self.metrics['connections_per_channel']),
            'messages_sent': self.metrics['messages_sent'],
            'messages_received': self.metrics['messages_received'],
            'errors': self.metrics['errors'],
            'uptime': (datetime.now() - self.metrics['start_time']).total_seconds(),
            'system_metrics': await self._get_system_metrics(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Verificar alertas en segundo plano
        asyncio.create_task(alert_system.check_thresholds(metrics))
        
        return metrics
```

## **4. REPORTES AUTOMÁTICOS**

### **4.1. Generación de Reportes Diarios**

```python
# monitoring/reports.py
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

class ReportGenerator:
    def __init__(self):
        self.report_data = []
    
    async def generate_daily_report(self):
        """Generar reporte diario automático"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # Recopilar datos del período
        report_data = {
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'summary': await self._generate_summary(start_time, end_time),
            'charts': await self._generate_charts(start_time, end_time),
            'top_channels': await self._get_top_channels(start_time, end_time),
            'issues_detected': await self._detect_issues(start_time, end_time)
        }
        
        # Guardar reporte
        self._save_report(report_data)
        
        # Enviar por email
        await self._send_report_email(report_data)
        
        return report_data
    
    async def _generate_summary(self, start_time, end_time):
        """Generar resumen ejecutivo"""
        connections = [c for c in self.monitor.connection_history 
                     if start_time <= c['connected_at'] <= end_time]
        
        return {
            'total_connections': len(connections),
            'unique_users': len(set(c.get('user_id') for c in connections if c.get('user_id'))),
            'total_messages': self.monitor.metrics['messages_sent'] + self.monitor.metrics['messages_received'],
            'avg_connection_duration': sum(c.get('duration', 0) for c in connections) / max(len(connections), 1),
            'error_rate': (self.monitor.metrics['errors'] / max(self.monitor.metrics['messages_sent'], 1)) * 100
        }
    
    async def _generate_charts(self, start_time, end_time):
        """Generar gráficas para el reporte"""
        # Crear gráfica de conexiones por hora
        hours = pd.date_range(start_time, end_time, freq='H')
        connections_by_hour = []
        
        for hour in hours:
            count = len([c for c in self.monitor.connection_history 
                       if hour <= c['connected_at'] < hour + timedelta(hours=1)])
            connections_by_hour.append({'hour': hour, 'connections': count})
        
        # Generar imagen de la gráfica
        plt.figure(figsize=(10, 6))
        plt.plot([h['hour'] for h in connections_by_hour], [h['connections'] for h in connections_by_hour])
        plt.title('Conexiones por Hora')
        plt.xticks(rotation=45)
        
        # Convertir a base64 para email
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        img_str = base64.b64encode(img_buffer.read()).decode()
        
        return {'connections_chart': f'data:image/png;base64,{img_str}'}
    
    async def _get_top_channels(self, start_time, end_time):
        """Canales más activos"""
        channel_stats = {}
        for conn in self.monitor.connection_history:
            if start_time <= conn['connected_at'] <= end_time:
                channel = conn['channel']
                channel_stats[channel] = channel_stats.get(channel, 0) + 1
        
        return sorted(channel_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    
    async def _detect_issues(self, start_time, end_time):
        """Detectar problemas en el período"""
        issues = []
        
        # Buscar períodos de alta carga
        high_load_periods = await self._find_high_load_periods(start_time, end_time)
        if high_load_periods:
            issues.append({
                'type': 'high_load',
                'periods': high_load_periods,
                'message': 'Períodos de alta carga detectados'
            })
        
        return issues
    
    def _save_report(self, report_data):
        """Guardar reporte en base de datos"""
        # Implementar según tu sistema de almacenamiento
        pass
    
    async def _send_report_email(self, report_data):
        """Enviar reporte por email"""
        # Implementar envío de email con el reporte
        pass

# Tarea programada para reportes diarios
async def scheduled_reports():
    report_generator = ReportGenerator()
    while True:
        try:
            # Esperar hasta las 2 AM
            now = datetime.now()
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if now.hour >= 2:
                next_run += timedelta(days=1)
            
            wait_seconds = (next_run - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Generar reporte
            await report_generator.generate_daily_report()
            logger.info("Reporte diario generado y enviado")
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            await asyncio.sleep(3600)  # Reintentar en 1 hora
```

## **5. INTEGRACIÓN COMPLETA CON FASTAPI**

```python
# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from monitoring.websocket_monitor import websocket_monitor
from monitoring.reports import scheduled_reports
from monitoring.alerts import alert_system

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Iniciar tareas en segundo plano al iniciar la aplicación
    monitor_task = asyncio.create_task(websocket_monitor.start_monitoring())
    report_task = asyncio.create_task(scheduled_reports())
    alert_task = asyncio.create_task(alert_system.start_alert_monitoring())
    
    yield
    
    # Limpiar al cerrar la aplicación
    monitor_task.cancel()
    report_task.cancel()
    alert_task.cancel()
    try:
        await asyncio.gather(monitor_task, report_task, alert_task, return_exceptions=True)
    except:
        pass

app = FastAPI(lifespan=lifespan)

# Importar routers
from presentation.api.monitoring_routes import monitoring_router
from presentation.websocket.routes import websocket_router

app.include_router(monitoring_router)
app.include_router(websocket_router)

@app.get("/")
async def root():
    return {
        "message": "Sistema WebSocket con Monitoreo",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }
```

## **6. BENEFICIOS DEL SISTEMA DE MONITOREO**

### **6.1. Visibilidad Completa**
- ✅ Métricas en tiempo real de conexiones WebSocket
- ✅ Monitoreo de rendimiento del sistema
- ✅ Detección temprana de problemas

### **6.2. Alertas Proactivas**
- ✅ Notificaciones automáticas por múltiples canales
- ✅ Umbrales configurables para diferentes métricas
- ✅ Prevención de spam de alertas con cooldowns

### **6.3. Reportes Automáticos**
- ✅ Reportes diarios de rendimiento
- ✅ Análisis histórico de conexiones
- ✅ Identificación de patrones y tendencias

### **6.4. Escalabilidad**
- ✅ Diseñado para alto volumen de conexiones
- ✅ Bajo overhead en el sistema principal
- ✅ Fácil integración con herramientas existentes

Este sistema de monitoreo proporciona una visión completa del estado de tus WebSockets en tiempo real, con alertas proactivas y reportes automáticos para mantener tu aplicación funcionando optimalmente.