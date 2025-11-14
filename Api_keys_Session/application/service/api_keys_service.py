import asyncio
from typing import List, Optional, Dict, Any
from ...domain.entities.repositories.api_keys_repository import APIKeyRepository
from ...application.use_cases.create_api_keys import CreateAPIKeyUseCase
from ...application.use_cases.validate_api_keys import ValidateAPIKeyUseCase

class APIKeyService:
    def __init__(self, api_key_repository: APIKeyRepository):
        print("[APIKeyService] Inicializando servicio... repositorio recibido:", api_key_repository)
        self.repository = api_key_repository
        self._cleanup_task = None
        self._start_cleanup_task()
        print("[APIKeyService] Servicio inicializado correctamente.")

    # --------------------------------------------------------
    # LIMPIEZA AUTOMÁTICA
    # --------------------------------------------------------
    def _start_cleanup_task(self):
        """Inicia la tarea automática de limpieza"""
        print("[APIKeyService] Iniciando tarea automática de limpieza...")
        
        async def cleanup_loop():
            while True:
                try:
                    print("[Cleanup] Ejecutando limpieza de claves expiradas...")
                    deleted = await self.repository.delete_expired()
                    print(f"[Cleanup] Limpieza completada. Claves eliminadas: {deleted}")
                    await asyncio.sleep(3600)  # Cada hora
                except Exception as e:
                    print(f"[Cleanup] Error en limpieza automática: {e}")
                    await asyncio.sleep(300)
        
        try:
            self._cleanup_task = asyncio.create_task(cleanup_loop())
            print("[APIKeyService] Tarea de limpieza iniciada correctamente.")
        except Exception as e:
            print("[APIKeyService] ERROR al iniciar limpieza automática:", str(e))

    async def stop_cleanup(self):
        """Detiene la limpieza automática"""
        print("[APIKeyService] Deteniendo tarea automática de limpieza...")
        if self._cleanup_task:
            try:
                self._cleanup_task.cancel()
                print("[APIKeyService] Tarea de limpieza cancelada correctamente.")
            except Exception as e:
                print("[APIKeyService] ERROR al cancelar la tarea de limpieza:", str(e))

    # --------------------------------------------------------
    # CREACIÓN DE API KEYS
    # --------------------------------------------------------
    async def create_key(
        self,
        user_id: str,
        permissions: List[str] = None,
        expires_in_days: int = 10,
        name: str = None,
        description: str = None
    ) -> Dict[str, Any]:
        print(f"[APIKeyService] create_key() llamado con user_id={user_id}, permissions={permissions}, "
              f"expires_in_days={expires_in_days}, name={name}, description={description}")
        try:
            use_case = CreateAPIKeyUseCase(self.repository)
            result = await use_case.execute(user_id, permissions, expires_in_days, name, description)
            print("[APIKeyService] API Key creada exitosamente:", result)
            return result
        except Exception as e:
            print(f"[APIKeyService] ERROR al crear API Key para user_id={user_id}: {str(e)}")
            raise

    # --------------------------------------------------------
    # VALIDACIÓN DE API KEYS
    # --------------------------------------------------------
    async def validate_key(self, key: str) -> Optional[Dict[str, Any]]:
        print(f"[APIKeyService] validate_key() llamado para key={key}")

        try:
            use_case = ValidateAPIKeyUseCase(self.repository)
            result = await use_case.execute(key)
            print(f"[APIKeyService] Resultado de validación para key={key}:", result)
            return result
        except Exception as e:
            print(f"[APIKeyService] ERROR al validar la API Key={key}: {str(e)}")
            raise

    # --------------------------------------------------------
    # LISTAR KEYS DE USUARIO
    # --------------------------------------------------------
    async def get_user_keys(self, user_id: str) -> List[Dict[str, Any]]:
        print(f"[APIKeyService] get_user_keys() llamado para user_id={user_id}")
        try:
            entities = await self.repository.find_by_user_id(user_id)
            result = [self._entity_to_dict(entity) for entity in entities]
            print(f"[APIKeyService] Keys encontradas para user_id={user_id}:", result)
            return result
        except Exception as e:
            print(f"[APIKeyService] ERROR al obtener keys del usuario {user_id}: {str(e)}")
            raise

    # --------------------------------------------------------
    # LIMPIEZA FORZADA
    # --------------------------------------------------------
    async def force_cleanup(self) -> int:
        """Fuerza limpieza inmediata"""
        print("[APIKeyService] force_cleanup() llamado.")
        try:
            deleted = await self.repository.delete_expired()
            print(f"[APIKeyService] Limpieza forzada completada. Claves eliminadas: {deleted}")
            return deleted
        except Exception as e:
            print("[APIKeyService] ERROR en limpieza forzada:", str(e))
            raise

    # --------------------------------------------------------
    # ESTADÍSTICAS
    # --------------------------------------------------------
    async def get_stats(self) -> Dict[str, Any]:
        print("[APIKeyService] get_stats() llamado.")
        try:
            stats = await self.repository.get_stats()
            print("[APIKeyService] Estadísticas obtenidas:", stats)
            return stats
        except Exception as e:
            print("[APIKeyService] ERROR al obtener estadísticas:", str(e))
            raise

    # --------------------------------------------------------
    # ENTIDAD → DICCIONARIO
    # --------------------------------------------------------
    def _entity_to_dict(self, entity) -> Dict[str, Any]:
        print("[APIKeyService] Transformando entidad a diccionario:", entity)
        try:
            result = {
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
            print("[APIKeyService] Transformación exitosa:", result)
            return result
        except Exception as e:
            print("[APIKeyService] ERROR al transformar entidad a dict:", str(e))
            raise
