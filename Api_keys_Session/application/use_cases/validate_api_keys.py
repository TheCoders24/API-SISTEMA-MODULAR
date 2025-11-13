from datetime import datetime
import hashlib
from typing import Optional, Dict, Any
from ...domain.entities.repositories.api_keys_repository import APIKeyRepository

class ValidateAPIKeyUseCase:
    def __init__(self, api_key_repository: APIKeyRepository):
        print("[ValidateAPIKeyUseCase] Inicializando con repositorio:", api_key_repository)
        self.api_key_repository = api_key_repository
        print("[ValidateAPIKeyUseCase] Repositorio configurado correctamente.")

    def hash_key(self, key: str) -> str:
        print("[ValidateAPIKeyUseCase] Hasheando key recibida...")
        hashed = hashlib.sha256(key.encode()).hexdigest()
        print("[ValidateAPIKeyUseCase] Hash generado:", hashed)
        return hashed

    async def execute(self, key: str) -> Optional[Dict[str, Any]]:
        print("[ValidateAPIKeyUseCase] Ejecutando validación de API Key...")
        print(f"[ValidateAPIKeyUseCase] Key recibida -> {key}")

        try:
            hashed_key = self.hash_key(key)
            print("[ValidateAPIKeyUseCase] Buscando key hasheada en repositorio:", hashed_key)

            entity = await self.api_key_repository.find_by_hashed_key(hashed_key)
            print("[ValidateAPIKeyUseCase] Resultado de la búsqueda:", entity)

            if not entity:
                print("[ValidateAPIKeyUseCase] ❌ No se encontró ninguna API Key con ese hash.")
                return None

            if not entity.is_valid():
                print("[ValidateAPIKeyUseCase] ❌ API Key encontrada pero inválida (expirada o inactiva).")
                return None

            print("[ValidateAPIKeyUseCase] ✅ API Key válida. Actualizando last_used...")

            # Actualizar last_used
            entity.last_used = datetime.utcnow()
            await self.api_key_repository.update(entity)

            print("[ValidateAPIKeyUseCase] last_used actualizado a:", entity.last_used)

            response = {
                "id": entity.id,
                "user_id": entity.user_id,
                "permissions": entity.permissions,
                "created_at": entity.created_at,
                "expires_at": entity.expires_at,
                "is_active": entity.is_active,
                "last_used": entity.last_used,
                "name": entity.name,
                "description": entity.description
            }

            print("[ValidateAPIKeyUseCase] Respuesta final generada:", response)
            return response

        except Exception as e:
            print("[ValidateAPIKeyUseCase] ERROR durante la ejecución:", str(e))
            raise
