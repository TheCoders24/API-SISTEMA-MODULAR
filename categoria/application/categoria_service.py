from ..infraestructura.categoria_repository import CategoriaRepository
from ..domain.models import Categoria  # Importamos el modelo
from typing import Optional

class CategoriaService:
    def __init__(self, categoria_repository: CategoriaRepository):
        self.categoria_repository = categoria_repository

    async def obtener_todas_categorias(self) -> list[Categoria]: # type: ignore
        """Obtiene todas las categorías existentes"""
        return await self.categoria_repository.listar_todos()
    
    async def obtener_categoria_por_id(self, categoria_id: int) -> Optional[Categoria]: # type: ignore
        """Obtiene una categoría por su ID"""
        return await self.categoria_repository.obtener_por_id(categoria_id)
    
    async def obtener_categoria_por_nombre(self, nombre: str) -> Optional[Categoria]: # type: ignore
        """Obtiene una categoría por su nombre (único)"""
        return await self.categoria_repository.obtener_por_nombre(nombre)
    
    async def crear_categoria(self, nombre: str) -> Categoria:
        """Crea una nueva categoría"""
        # Verificamos si ya existe una categoría con ese nombre
        if await self.obtener_categoria_por_nombre(nombre):
            raise ValueError("Ya existe una categoría con este nombre")
        
        return await self.categoria_repository.crear(nombre=nombre)
    
    async def actualizar_categoria(self, categoria_id: int, nuevo_nombre: str) -> Categoria:
        """Actualiza el nombre de una categoría existente"""
        # Verificamos si el nuevo nombre ya está en uso
        if await self.obtener_categoria_por_nombre(nuevo_nombre):
            raise ValueError("Ya existe una categoría con este nombre")
            
        return await self.categoria_repository.actualizar(categoria_id, nuevo_nombre)
    
    async def eliminar_categoria(self, categoria_id: int) -> bool:
        """Elimina una categoría por su ID"""
        return await self.categoria_repository.eliminar(categoria_id)
