class VentaError(Exception):
    """Base exception for ventas domain"""

class StockInsuficienteError(VentaError):
    def __init__(self, producto_nombre: str, stock_actual: int, cantidad_solicitada: int):
        self.producto_nombre = producto_nombre
        self.stock_actual = stock_actual
        self.cantidad_solicitada = cantidad_solicitada
        super().__init__(f"Stock insuficiente para {producto_nombre}. Stock actual: {stock_actual}, solicitado: {cantidad_solicitada}")

class ProductoNoEncontradoError(VentaError):
    def __init__(self, producto_id: int):
        self.producto_id = producto_id
        super().__init__(f"Producto con ID {producto_id} no encontrado")

class VentaNoEncontradaError(VentaError):
    def __init__(self, venta_id: int):
        self.venta_id = venta_id
        super().__init__(f"Venta con ID {venta_id} no encontrada")