from datetime import datetime, timedelta
import secrets
import hashlib
from typing import Dict, Any, List, Optional
from ...domain.entities.api_keys import APIKeyEntity
from ...domain.entities.repositories.api_keys_repository import APIKeyRepository
from ...presentation.schemas.api_keys_schemas import APIKeyCreate


class CreateAPIKeyUseCase:
    def __init__(self, api_key_repository: APIKeyRepository):
        print("[CreateAPIKeyUseCase] Inicializando con repositorio:", api_key_repository)
        self.api_key_repository = api_key_repository
        print("[CreateAPIKeyUseCase] Repositorio configurado correctamente.")

    def generate_key(self) -> str:
        """Genera una API key aleatoria"""
        print("[CreateAPIKeyUseCase] Generando API Key aleatoria...")
        key = secrets.token_urlsafe(32)
        print("[CreateAPIKeyUseCase] API Key generada:", key)
        return key

    def hash_key(self, key: str) -> str:
        """Hashea la API key con SHA256"""
        print("[CreateAPIKeyUseCase] Hasheando API Key...")
        hashed = hashlib.sha256(key.encode()).hexdigest()
        print("[CreateAPIKeyUseCase] API Key hasheada:", hashed)
        return hashed

    async def execute(
        self,
        user_id: str,
        permissions: Optional[List[str]] = None,
        expires_in_days: int = 30,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Crea una nueva API Key para el usuario especificado"""

        print(f"[CreateAPIKeyUseCase] Ejecutando creación de API Key para user_id={user_id}")
        print(f"[CreateAPIKeyUseCase] Parámetros -> permissions={permissions}, expires_in_days={expires_in_days}, "
              f"name={name}, description={description}")

        try:
            raw_key = self.generate_key()
            hashed_key = self.hash_key(raw_key)

            print("[CreateAPIKeyUseCase] Construyendo entidad APIKeyEntity...")
            api_key_entity = APIKeyEntity(
                id=None,
                user_id=str(user_id),
                hashed_key=hashed_key,
                permissions=permissions or ["default"],
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
                is_active=True,
                name=name,
                description=description,
            )
            print("[CreateAPIKeyUseCase] Entidad creada:", api_key_entity)

            print("[CreateAPIKeyUseCase] Guardando entidad en el repositorio...")
            saved_entity = await self.api_key_repository.create(api_key_entity)
            print("[CreateAPIKeyUseCase] Entidad guardada exitosamente:", saved_entity)

            # Manejo flexible: dict o entidad
            if isinstance(saved_entity, dict):
                print("[CreateAPIKeyUseCase] Respuesta del repositorio es dict")
                key_id = saved_entity.get("id")
                expires_at = saved_entity.get("expires_at")
                permissions = saved_entity.get("permissions", [])
                is_active = saved_entity.get("is_active", True)
            else:
                print("[CreateAPIKeyUseCase] Respuesta del repositorio es entidad")
                key_id = getattr(saved_entity, "id", None)
                expires_at = getattr(saved_entity, "expires_at", None)
                permissions = getattr(saved_entity, "permissions", [])
                is_active = getattr(saved_entity, "is_active", True)

            response = {
                "key_id": key_id,
                "raw_key": raw_key,
                "expires_at": expires_at,
                "permissions": permissions,
                "is_active": is_active,
            }

            print("[CreateAPIKeyUseCase] Resultado final a retornar:", response)
            return response

        except Exception as e:
            print("[CreateAPIKeyUseCase] ERROR en execute():", str(e))
            raise
