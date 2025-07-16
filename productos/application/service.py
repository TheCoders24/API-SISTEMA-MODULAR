from typing import Optional
from fastapi import HTTPException, status
from ..presentation import schemas

class ProductService:
    def __init__(self, repository):
        self.repository = repository
    
    async def create_product(self, data: schemas.ProductoCreate):
        # Validación de negocio
        if await self.repository.get_by_name(data.nombre):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un producto con ese nombre"
            )
        
        # Creación del producto
        return await self.repository.create(data.dict())
    
    async def get_product(self, id: int):
        product = await self.repository.get_by_id(id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        return product
    
    # Obtener todos los productos de la tabla productos
    async def get_all_products(self) -> list[schemas.Producto]:
        """Obtiene todos los productos con validación"""
        try:
            products = await self.repository.obtener_todos_productos()
            return [schemas.Producto(**product) for product in products]
        except Exception as e:
            raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener listado de productos: {str(e)}"
        )

    async def get_product_nom(self, nombre: str):
        product = await self.repository.get_by_nombre(nombre)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        return product          

    async def get_product_by_id(self, product_id: int) -> Optional[schemas.Producto]:
        """Obtiene un producto por ID con validación"""
        # Validación del ID
        if product_id <= 0:
            raise ValueError("ID de producto inválido")
        
        # Obtener el producto del repositorio
        producto = await self.repository.get_by_id(product_id)  # Fixed variable name
        
        # Verificar si el producto existe
        if not producto:  # Check the product object, not the ID
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
    
        return producto  # Return the product object, not the ID
    
    async def delete_product(self, product_id: int) -> bool:
        """Elimina un producto por ID"""
        product = await self.get_product_by_id(product_id)
        if not product:
            return False
        
        await self.repository.delete(product)  # Pasamos el objeto Producto, no el ID
        return True