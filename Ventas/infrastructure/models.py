from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel

Base = declarative_base()


# model pydantic para respuesta de ventas
class DetalleVentaResponse(BaseModel):
    id: int
    producto_id: int
    cantidad: int
    precio: float
    producto_nombre: str  # Necesitarás agregar esto en tu query
    
    class Config:
        from_attributes = True

class VentaResponse(BaseModel):
    id: int
    fecha: datetime
    total: float
    usuario_id: Optional[int] = None
    detalles: List[DetalleVentaResponse]
    
    class Config:
        from_attributes = True

class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    total = Column(DECIMAL(10, 2), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="ventas")
    detalles = relationship("DetalleVenta", back_populates="venta", cascade="all, delete-orphan")

class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"

    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio = Column(DECIMAL(10, 2), nullable=False)
    
    # Relaciones
    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalle_ventas")

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio = Column(DECIMAL(10, 2), nullable=False)
    stock = Column(Integer, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    
    # Relaciones
    categoria = relationship("Categoria", back_populates="productos")
    proveedor = relationship("Proveedor", back_populates="productos")
    detalle_ventas = relationship("DetalleVenta", back_populates="producto")
    movimientos = relationship("Movimiento", back_populates="producto")
    historial_precios = relationship("HistorialPrecio", back_populates="producto")

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=True)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    ventas = relationship("Venta", back_populates="usuario")
    movimientos = relationship("Movimiento", back_populates="usuario")
    devoluciones = relationship("Devolucion", back_populates="usuario")
    usuarios_roles = relationship("UsuarioRol", back_populates="usuario")
    sesiones = relationship("Sesion", back_populates="usuario")
    historial_precios = relationship("HistorialPrecio", back_populates="usuario")

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    
    # Relaciones
    productos = relationship("Producto", back_populates="categoria")

class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    contacto = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(100))
    
    # Relaciones
    productos = relationship("Producto", back_populates="proveedor")
    pedidos_proveedores = relationship("PedidoProveedor", back_populates="proveedor")

class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(20), nullable=False)
    cantidad = Column(Integer, nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Relaciones
    producto = relationship("Producto", back_populates="movimientos")
    usuario = relationship("Usuario", back_populates="movimientos")

class Rol(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(20), nullable=False, unique=True)
    
    # Relaciones
    usuarios_roles = relationship("UsuarioRol", back_populates="rol")

class UsuarioRol(Base):
    __tablename__ = "usuarios_roles"

    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="usuarios_roles")
    rol = relationship("Rol", back_populates="usuarios_roles")

class PedidoProveedor(Base):
    __tablename__ = "pedidos_proveedores"

    id = Column(Integer, primary_key=True, index=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id", ondelete="CASCADE"), nullable=False)
    fecha_pedido = Column(DateTime(timezone=True), server_default=func.now())
    fecha_entrega = Column(DateTime(timezone=True))
    total = Column(DECIMAL(10, 2), nullable=False)
    
    # Relaciones
    proveedor = relationship("Proveedor", back_populates="pedidos_proveedores")
    detalle_pedidos = relationship("DetallePedidoProveedor", back_populates="pedido")

class DetallePedidoProveedor(Base):
    __tablename__ = "detalle_pedidos_proveedores"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos_proveedores.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio = Column(DECIMAL(10, 2), nullable=False)
    
    # Relaciones
    pedido = relationship("PedidoProveedor", back_populates="detalle_pedidos")
    producto = relationship("Producto")

class Devolucion(Base):
    __tablename__ = "devoluciones"

    id = Column(Integer, primary_key=True, index=True)
    venta_id = Column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    motivo = Column(Text)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Relaciones
    venta = relationship("Venta")
    usuario = relationship("Usuario", back_populates="devoluciones")
    detalle_devoluciones = relationship("DetalleDevolucion", back_populates="devolucion")

class DetalleDevolucion(Base):
    __tablename__ = "detalle_devoluciones"

    id = Column(Integer, primary_key=True, index=True)
    devolucion_id = Column(Integer, ForeignKey("devoluciones.id", ondelete="CASCADE"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio = Column(DECIMAL(10, 2), nullable=False)
    
    # Relaciones
    devolucion = relationship("Devolucion", back_populates="detalle_devoluciones")
    producto = relationship("Producto")

class HistorialPrecio(Base):
    __tablename__ = "historial_precios"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id", ondelete="CASCADE"), nullable=False)
    precio_anterior = Column(DECIMAL(10, 2), nullable=False)
    precio_nuevo = Column(DECIMAL(10, 2), nullable=False)
    fecha_cambio = Column(DateTime(timezone=True), server_default=func.now())
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Relaciones
    producto = relationship("Producto", back_populates="historial_precios")
    usuario = relationship("Usuario", back_populates="historial_precios")

class Sesion(Base):
    __tablename__ = "sesiones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(512), nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True))
    activa = Column(Boolean, default=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="sesiones")

class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    tabla_afectada = Column(String(100), nullable=False)
    accion = Column(String(20), nullable=False)
    id_registro = Column(Integer, nullable=False)
    usuario_nombre = Column(String(100))
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    detalles = Column(Text)

class Configuracion(Base):
    __tablename__ = "configuraciones"

    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String(100), nullable=False, unique=True)
    valor = Column(Text, nullable=False)
    descripcion = Column(Text)

class Metrica(Base):
    __tablename__ = "metricas"

    id = Column(Integer, primary_key=True, index=True)
    tipo_metrica = Column(String(50), nullable=False)
    valor = Column(Text, nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())

class RegistroActividad(Base):
    __tablename__ = "registro_actividad"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    ip = Column(String(45), nullable=False)
    fecha = Column(DateTime, server_default=func.now())
    accion = Column(String(50), nullable=False)