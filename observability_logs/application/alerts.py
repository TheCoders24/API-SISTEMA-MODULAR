# C:\Users\ALEXIS\Desktop\API-SISTEMA-MODULAR\observability_logs\application\alerts.py

from typing import List, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass
from ..domain.events import SecurityAlertTriggered  # ✅ CORRECTO



@dataclass
class AlertRule:
    """Regla para detectar comportamientos anómalos"""
    # 🔥 CORREGIDO: Orden correcto
    name: str  # ← SIN DEFAULT
    severity: str  # ← SIN DEFAULT
    condition: Callable  # ← SIN DEFAULT
    description: str = ""  # ← CON DEFAULT


class SecurityAlertService:
    """Servicio que analiza logs y dispara alertas - SIN NOTIFICADORES"""
    
    def __init__(self, log_repository):
        self.log_repo = log_repository
        self._setup_rules()
    
    def _setup_rules(self):
        self.rules = [
            AlertRule(
                name="BRUTE_FORCE_ATTACK",
                severity="CRITICAL",
                description="Múltiples intentos fallidos desde misma IP",
                condition=self._detect_brute_force
            ),
            AlertRule(
                name="PORT_SCAN_DETECTED",
                severity="HIGH",
                description="Acceso a múltiples endpoints en poco tiempo",
                condition=self._detect_port_scan
            ),
            AlertRule(
                name="UNUSUAL_HOURS_ACCESS",
                severity="MEDIUM",
                description="Acceso fuera de horario laboral",
                condition=self._detect_unusual_hours
            ),
            AlertRule(
                name="MULTIPLE_FAILURES",
                severity="HIGH",
                description="Múltiples fallos en diferentes servicios",
                condition=self._detect_multiple_failures
            )
        ]
    
    def _detect_brute_force(self, logs: List[Any]) -> bool:
        """+10 intentos fallidos en 1 minuto desde misma IP"""
        ip_failures = defaultdict(int)
        one_min_ago = datetime.utcnow() - timedelta(minutes=1)
        
        for log in logs:
            if (hasattr(log, 'category') and log.category == "security" and
                hasattr(log, 'action') and "FAILED" in log.action and
                hasattr(log, 'timestamp') and log.timestamp > one_min_ago and
                hasattr(log, 'ip') and log.ip):
                ip_failures[log.ip] += 1
        
        return any(count >= 10 for count in ip_failures.values())
    
    def _detect_port_scan(self, logs: List[Any]) -> bool:
        """+20 endpoints diferentes en 30 segundos desde misma IP"""
        ip_endpoints = defaultdict(set)
        thirty_sec_ago = datetime.utcnow() - timedelta(seconds=30)
        
        for log in logs:
            if (hasattr(log, 'timestamp') and log.timestamp > thirty_sec_ago and
                hasattr(log, 'ip') and log.ip and
                hasattr(log, 'endpoint') and log.endpoint):
                ip_endpoints[log.ip].add(log.endpoint)
        
        return any(len(endpoints) >= 20 for endpoints in ip_endpoints.values())
    
    def _detect_unusual_hours(self, logs: List[Any]) -> bool:
        """Acceso a admin fuera de horario (0-6)"""
        for log in logs:
            if (hasattr(log, 'category') and log.category == "authorization" and
                hasattr(log, 'action') and "ADMIN" in log.action and
                hasattr(log, 'timestamp') and log.timestamp):
                hour = log.timestamp.hour
                if hour < 6 or hour > 22:
                    return True
        return False
    
    def _detect_multiple_failures(self, logs: List[Any]) -> bool:
        """Usuario con +3 fallos en diferentes acciones"""
        user_failures = defaultdict(set)
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        
        for log in logs:
            if (hasattr(log, 'category') and log.category == "security" and
                hasattr(log, 'action') and "FAILED" in log.action and
                hasattr(log, 'user_id') and log.user_id and
                hasattr(log, 'timestamp') and log.timestamp > five_min_ago):
                user_failures[log.user_id].add(log.action)
        
        return any(len(actions) >= 3 for actions in user_failures.values())
    
    def analyze_and_alert(self, timeframe_minutes: int = 5) -> List[SecurityAlertTriggered]:
        """Analiza logs recientes y muestra alertas en consola"""
        cutoff = datetime.utcnow() - timedelta(minutes=timeframe_minutes)
        recent_logs = self.log_repo.get_since(cutoff)
        
        alerts_triggered = []
        
        for rule in self.rules:
            if rule.condition(recent_logs):
                alert = SecurityAlertTriggered(
                    alert_type=rule.name,
                    severity=rule.severity,
                    log_entries=recent_logs[:5],  # Solo primeros 5 para no saturar
                    metadata={
                        "rule": rule.name,
                        "description": rule.description,
                        "timeframe": f"{timeframe_minutes}min",
                        "total_logs_analyzed": len(recent_logs)
                    }
                )
                alerts_triggered.append(alert)
                
                # 🖥️ SOLO CONSOLA - SIN SLACK, SIN EMAIL
                print(f"\n🚨 ALERTA [{rule.severity}]: {rule.name}")
                print(f"   📝 {rule.description}")
                print(f"   ⏱️  {timeframe_minutes}min - {len(recent_logs)} logs analizados")
        
        return alerts_triggered