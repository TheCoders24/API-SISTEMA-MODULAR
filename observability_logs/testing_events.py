# test_events_definitivo.py
import sys
from pathlib import Path

# 🔥 RUTA CORRECTA - UNA SOLA VEZ
ROOT_DIR = Path(__file__).parent  # C:\Users\ALEXIS\Desktop\API-SISTEMA-MODULAR
sys.path.insert(0, str(ROOT_DIR))

print("🔍 VERIFICANDO ARCHIVO EVENTS.PY")
print("=" * 60)

# ✅ RUTA CORRECTA: observability_logs/domain/events.py (SIN DUPLICAR)
events_file = ROOT_DIR / "observability_logs" / "domain" / "events.py"
print(f"📁 Buscando en: {events_file}")

if events_file.exists():
    print("✅ Archivo encontrado!")
    content = events_file.read_text(encoding='utf-8')
    print("   ✓ events.py existe y se puede leer")
else:
    print(f"❌ Archivo NO encontrado")
    
    # Crear la estructura correcta AHORA MISMO
    print("\n🔧 CREANDO ESTRUCTURA CORRECTA...")
    
    # 1. Crear observability_logs/
    obs_dir = ROOT_DIR / "observability_logs"
    obs_dir.mkdir(exist_ok=True)
    print(f"   ✅ Creado: {obs_dir}/")
    
    # 2. Crear __init__.py
    init_file = obs_dir / "__init__.py"
    init_file.write_text('"""Módulo de observabilidad"""\n\n__version__ = "1.0.0"\n')
    print(f"   ✅ Creado: {init_file}")
    
    # 3. Crear domain/
    domain_dir = obs_dir / "domain"
    domain_dir.mkdir(exist_ok=True)
    print(f"   ✅ Creado: {domain_dir}/")
    
    # 4. Crear domain/__init__.py
    domain_init = domain_dir / "__init__.py"
    domain_init.touch()
    print(f"   ✅ Creado: {domain_init}")
    
    # 5. Crear events.py con el contenido CORRECTO
    events_content = '''from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class DomainEvent:
    """Base para todos los eventos de dominio"""
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LogCreated(DomainEvent):
    """Evento disparado cuando se crea un log"""
    log_entry: Any
    context: Optional[Dict[str, Any]] = None


@dataclass
class SecurityAlertTriggered(DomainEvent):
    """Evento para alertas de seguridad"""
    alert_type: str
    severity: str
    log_entries: List[Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetected(DomainEvent):
    """Evento para comportamientos anómalos"""
    anomaly_type: str
    confidence: float
    evidence: Dict[str, Any]
    suggested_action: Optional[str] = None
'''
    events_file.write_text(events_content)
    print(f"   ✅ Creado: {events_file}")
    print(f"   ✓ Contenido: LogCreated con log_entry ANTES que context")

# Ahora intentar importar
print("\n" + "=" * 60)
print("📦 Intentando importar observability_logs...")

try:
    from observability_logs.domain.events import LogCreated
    print("✅ IMPORTACIÓN EXITOSA")
    
    # Probar crear instancia
    log = LogCreated(log_entry="test")
    print(f"   ✅ LogCreated creado: log_entry='{log.log_entry}'")
    print(f"   ✅ context: {log.context}")
    print(f"   ✅ event_id: {log.event_id}")
    
    print("\n🎯 ¡TODO CORREGIDO! El módulo funciona correctamente.")
    print("    Ahora puedes ejecutar: python main.py")
    
except ImportError as e:
    print(f"\n❌ ERROR DE IMPORTACIÓN: {e}")
    print("\n🔍 VERIFICANDO PYTHONPATH:")
    print(f"   sys.path[0]: {sys.path[0]}")
    print(f"   ¿Es la raíz del proyecto? {sys.path[0] == str(ROOT_DIR)}")
    
except Exception as e:
    print(f"\n❌ OTRO ERROR: {e}")