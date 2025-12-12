```sql

ALTER TABLE usuarios
ADD COLUMN activo BOOLEAN DEFAULT TRUE;

Table Categorias {
  id SERIAL [pk]
  nombre VARCHAR(100) [unique]
}

Table Proveedores {
  id SERIAL [pk]
  nombre VARCHAR(100)
  contacto VARCHAR(100)
  telefono VARCHAR(20)
  email VARCHAR(100)
}

Table Usuarios {
  id SERIAL [pk]
  nombre VARCHAR(100)
  email VARCHAR(100) [unique]
  password VARCHAR(512)
  is_active BOOLEAN
  fecha_registro TIMESTAMP
}

Table Productos {
  id SERIAL [pk]
  nombre VARCHAR(100)
  descripcion TEXT
  precio DECIMAL(10,2)
  stock INT
  categoria_id INT
  proveedor_id INT
}

Table Ventas {
  id SERIAL [pk]
  fecha TIMESTAMP
  total DECIMAL(10,2)
  usuario_id INT
}

Table Detalle_Ventas {
  id SERIAL [pk]
  venta_id INT
  producto_id INT
  cantidad INT
  precio DECIMAL(10,2)
}

Table Movimientos {
  id SERIAL [pk]
  producto_id INT
  tipo VARCHAR(20) // 'entrada' o 'salida'
  cantidad INT
  fecha TIMESTAMP
  usuario_id INT
}

Table Pedidos_Proveedores {
  id SERIAL [pk]
  proveedor_id INT
  fecha_pedido TIMESTAMP
  fecha_entrega TIMESTAMP
  total DECIMAL(10,2)
}

Table Detalle_Pedidos_Proveedores {
  id SERIAL [pk]
  pedido_id INT
  producto_id INT
  cantidad INT
  precio DECIMAL(10,2)
}

Table Devoluciones {
  id SERIAL [pk]
  venta_id INT
  fecha TIMESTAMP
  motivo TEXT
  usuario_id INT
}

Table Detalle_Devoluciones {
  id SERIAL [pk]
  devolucion_id INT
  producto_id INT
  cantidad INT
  precio DECIMAL(10,2)
}

Table Auditoria {
  id SERIAL [pk]
  tabla_afectada VARCHAR(100)
  accion VARCHAR(20) // 'INSERT', 'UPDATE', 'DELETE'
  id_registro INT
  usuario_nombre VARCHAR(100)
  fecha TIMESTAMP
  detalles TEXT
}

Ref: Productos.categoria_id > Categorias.id
Ref: Productos.proveedor_id > Proveedores.id
Ref: Ventas.usuario_id > Usuarios.id
Ref: Detalle_Ventas.venta_id > Ventas.id
Ref: Detalle_Ventas.producto_id > Productos.id
Ref: Movimientos.producto_id > Productos.id
Ref: Movimientos.usuario_id > Usuarios.id
Ref: Pedidos_Proveedores.proveedor_id > Proveedores.id
Ref: Detalle_Pedidos_Proveedores.pedido_id > Pedidos_Proveedores.id
Ref: Detalle_Pedidos_Proveedores.producto_id > Productos.id
Ref: Devoluciones.venta_id > Ventas.id
Ref: Devoluciones.usuario_id > Usuarios.id
Ref: Detalle_Devoluciones.devolucion_id > Devoluciones.id
Ref: Detalle_Devoluciones.producto_id > Productos.id
```