from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from ..domain.models import Categoria
import logging

logger = logging.getLogger(__name__)

class CategoriaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def listar_todos(self) -> list[Categoria]: # type: ignore
        """Obtiene todas las categorías"""
        result = await self.session.execute(select(Categoria))
        return result.scalars().all()
    
    async def obtener_por_id(self, categoria_id: int) -> Categoria | None: # type: ignore
        """Obtiene una categoría por su ID"""
        result = await self.session.execute(
            select(Categoria).where(Categoria.id == categoria_id)
        )
        return result.scalar_one_or_none()
    
    async def obtener_por_nombre(self, nombre: str) -> Categoria | None: # type: ignore
        """Obtiene una categoría por su nombre"""
        result = await self.session.execute(
            select(Categoria).where(Categoria.nombre == nombre)
        )
        return result.scalar_one_or_none()
    
    async def crear(self, nombre: str) -> Categoria:
        """Crea una nueva categoría"""
        try:
            nueva_categoria = Categoria(nombre=nombre)
            self.session.add(nueva_categoria)
            await self.session.commit()
            await self.session.refresh(nueva_categoria)
            return nueva_categoria
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La categoría '{nombre}' ya existe"
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creando categoría: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al crear categoría"
            )
    
    async def actualizar(self, categoria_id: int, nuevo_nombre: str) -> Categoria:
        """Actualiza una categoría existente"""
        try:
            categoria = await self.obtener_por_id(categoria_id)
            if not categoria:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada"
                )
            
            categoria.nombre = nuevo_nombre
            await self.session.commit()
            await self.session.refresh(categoria)
            return categoria
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La categoría '{nuevo_nombre}' ya existe"
            )
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error actualizando categoría: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al actualizar categoría"
            )
    
    async def eliminar(self, categoria_id: int) -> bool:
        """Elimina una categoría"""
        try:
            categoria = await self.obtener_por_id(categoria_id)
            if not categoria:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Categoría no encontrada"
                )
            
            await self.session.delete(categoria)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error eliminando categoría: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al eliminar categoría"
            )