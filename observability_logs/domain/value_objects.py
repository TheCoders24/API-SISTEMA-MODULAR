import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TraceID:
    """Value Object inmutable para TraceID"""
    value: str
    
    def __str__(self):
        return self.value
    
    @classmethod
    def generate(cls):
        return cls(uuid.uuid4().hex)


def generate_trace_id() -> str:
    """Función helper para generar trace_id"""
    return uuid.uuid4().hex