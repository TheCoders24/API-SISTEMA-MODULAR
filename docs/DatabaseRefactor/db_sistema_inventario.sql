

-- Tabla: Categorias
CREATE TABLE Categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Tabla: Proveedores
CREATE TABLE Proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    contacto VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(100)
);

-- Tabla: Usuarios
CREATE TABLE Usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(512) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: Productos
CREATE TABLE Productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) NOT NULL CHECK (precio >= 0),
    stock INT NOT NULL CHECK (stock >= 0),
    categoria_id INT REFERENCES Categorias(id) ON DELETE SET NULL,
    proveedor_id INT REFERENCES Proveedores(id) ON DELETE SET NULL
);

-- Tabla: Ventas
CREATE TABLE Ventas (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(10,2) NOT NULL CHECK (total >= 0),
    usuario_id INT REFERENCES Usuarios(id) ON DELETE SET NULL
);

-- Tabla: Detalle_Ventas
CREATE TABLE Detalle_Ventas (
    id SERIAL PRIMARY KEY,
    venta_id INT NOT NULL REFERENCES Ventas(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES Productos(id) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio DECIMAL(10,2) NOT NULL CHECK (precio >= 0)
);

-- Tabla: Movimientos
CREATE TABLE Movimientos (
    id SERIAL PRIMARY KEY,
    producto_id INT NOT NULL REFERENCES Productos(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('entrada', 'salida')),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT REFERENCES Usuarios(id) ON DELETE SET NULL
);

-- Tabla: Pedidos_Proveedores
CREATE TABLE Pedidos_Proveedores (
    id SERIAL PRIMARY KEY,
    proveedor_id INT NOT NULL REFERENCES Proveedores(id) ON DELETE CASCADE,
    fecha_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP,
    total DECIMAL(10,2) NOT NULL CHECK (total >= 0)
);

-- Tabla: Detalle_Pedidos_Proveedores
CREATE TABLE Detalle_Pedidos_Proveedores (
    id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL REFERENCES Pedidos_Proveedores(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES Productos(id) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio DECIMAL(10,2) NOT NULL CHECK (precio >= 0)
);

-- Tabla: Devoluciones
CREATE TABLE Devoluciones (
    id SERIAL PRIMARY KEY,
    venta_id INT NOT NULL REFERENCES Ventas(id) ON DELETE CASCADE,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    motivo TEXT,
    usuario_id INT REFERENCES Usuarios(id) ON DELETE SET NULL
);

-- Tabla: Detalle_Devoluciones
CREATE TABLE Detalle_Devoluciones (
    id SERIAL PRIMARY KEY,
    devolucion_id INT NOT NULL REFERENCES Devoluciones(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES Productos(id) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio DECIMAL(10,2) NOT NULL CHECK (precio >= 0)
);

-- Tabla: Auditoria
CREATE TABLE Auditoria (
    id SERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(100) NOT NULL,
    accion VARCHAR(20) NOT NULL CHECK (accion IN ('INSERT', 'UPDATE', 'DELETE')),
    id_registro INT NOT NULL,
    usuario_nombre VARCHAR(100),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    detalles TEXT
);