import logging
from typing import Optional, List
from fastapi import HTTPException, status
from ..presentation import schemas

class ProductService:
    def __init__(self, repository):
        self.repository = repository
    
    async def create_product(self, data: schemas.ProductoCreate):
        if await self.repository.get_by_name(data.nombre):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un producto con ese nombre"
            )
        return await self.repository.create(data.dict())
    
    async def get_product(self, id: int) -> schemas.Producto:
        product = await self.repository.get_by_id(id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        return product
    
    async def get_all_products(self) -> List[schemas.Producto]:
        try:
            products = await self.repository.obtener_todos_productos()
            return [schemas.Producto(**product) for product in products]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener listado de productos: {str(e)}"
            )

    async def get_product_nom(self, nombre: str) -> schemas.Producto:
        product = await self.repository.get_by_name(nombre)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        return product          

    async def get_product_by_id(self, product_id: int) -> Optional[schemas.Producto]:
        if product_id <= 0:
            raise ValueError("ID de producto inválido")
        
        producto = await self.repository.get_by_id(product_id)
        
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
    
        return producto
    
    async def delete_product(self, product_id: int) -> bool:
        try:
            deleted = await self.repository.delete(product_id)
            return deleted
        except Exception as e:
            logging.error(f"Error al eliminar el producto: {str(e)}")
            return False
    
    async def update_product(self, product_id: int, data: schemas.ProductoUpdate) -> schemas.Producto:
        # Verificar si el producto existe
        existing_product = await self.repository.get_by_id(product_id)
        if not existing_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Verificar conflicto de nombre (si se está actualizando el nombre)
        if data.nombre and data.nombre != existing_product.nombre:
            if await self.repository.get_by_name(data.nombre):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un producto con ese nombre"
                )
        
        # Actualizar el producto
        try:
            updated_product = await self.repository.update(product_id, data.dict(exclude_unset=True))
            return updated_product
        except Exception as e:
            logging.error(f"Error al actualizar el producto: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al actualizar el producto"
            )
