# reportes/__init__.py
"""
Módulo de Reportes - Clean Architecture
"""

# reportes/application/__init__.py
"""
Capa de aplicación - Casos de uso y DTOs
"""

# reportes/domain/__init__.py
"""
Capa de dominio - Entidades, repositorios abstractos y servicios de dominio
"""

# reportes/infrastructure/__init__.py
"""
Capa de infraestructura - Implementaciones concretas
"""

# reportes/models/__init__.py
"""
Modelos de datos (opcional)
"""

# reportes/presentation/__init__.py
"""
Capa de presentación - Endpoints FastAPI
"""


from .presentation.routes import routes_reportes_metricas

__all__ = ["router"]