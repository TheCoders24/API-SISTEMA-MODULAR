
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
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(512) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
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
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('entrada','salida')),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT REFERENCES Usuarios(id) ON DELETE SET NULL
);

-- Tabla: Pedidos_Proveedores
CREATE TABLE Pedidos_Proveedores (
    id SERIAL PRIMARY KEY,
    proveedor_id INT NOT NULL REFERENCES Proveedores(id) ON DELETE CASCADE,
    fecha_pedido TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
    accion VARCHAR(20) NOT NULL CHECK (accion IN ('INSERT','UPDATE','DELETE')),
    id_registro INT NOT NULL,
    usuario_nombre VARCHAR(100),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    detalles TEXT
);





-- Índices para consultas frecuentes
CREATE INDEX idx_productos_categoria ON Productos(categoria_id);
CREATE INDEX idx_productos_proveedor ON Productos(proveedor_id);
CREATE INDEX idx_ventas_fecha ON Ventas(fecha);
CREATE INDEX idx_ventas_usuario ON Ventas(usuario_id);
CREATE INDEX idx_detalle_ventas_venta ON Detalle_Ventas(venta_id);
CREATE INDEX idx_detalle_ventas_producto ON Detalle_Ventas(producto_id);
CREATE INDEX idx_movimientos_producto_fecha ON Movimientos(producto_id, fecha);
CREATE INDEX idx_auditoria_fecha ON Auditoria(fecha);
CREATE INDEX idx_auditoria_tabla ON Auditoria(tabla_afectada);


-- Trigger para actualizar stock automáticamente
CREATE OR REPLACE FUNCTION actualizar_stock()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'detalle_ventas' THEN
        UPDATE Productos 
        SET stock = stock - NEW.cantidad 
        WHERE id = NEW.producto_id;
    ELSIF TG_TABLE_NAME = 'movimientos' AND NEW.tipo = 'entrada' THEN
        UPDATE Productos 
        SET stock = stock + NEW.cantidad 
        WHERE id = NEW.producto_id;
    ELSIF TG_TABLE_NAME = 'movimientos' AND NEW.tipo = 'salida' THEN
        UPDATE Productos 
        SET stock = stock - NEW.cantidad 
        WHERE id = NEW.producto_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_actualizar_stock_ventas
    AFTER INSERT ON Detalle_Ventas
    FOR EACH ROW EXECUTE FUNCTION actualizar_stock();

CREATE TRIGGER tr_actualizar_stock_movimientos
    AFTER INSERT ON Movimientos
    FOR EACH ROW EXECUTE FUNCTION actualizar_stock();





-- Vista para reporte de ventas
CREATE VIEW vista_ventas_detalladas AS
SELECT 
    v.id,
    v.fecha,
    u.nombre as vendedor,
    v.total,
    COUNT(dv.id) as cantidad_productos,
    STRING_AGG(p.nombre, ', ') as productos
FROM Ventas v
JOIN Usuarios u ON v.usuario_id = u.id
JOIN Detalle_Ventas dv ON v.id = dv.venta_id
JOIN Productos p ON dv.producto_id = p.id
GROUP BY v.id, v.fecha, u.nombre, v.total;

-- Vista para stock bajo
CREATE VIEW vista_stock_bajo AS
SELECT 
    p.id,
    p.nombre,
    p.stock,
    c.nombre as categoria,
    pr.nombre as proveedor
FROM Productos p
JOIN Categorias c ON p.categoria_id = c.id
JOIN Proveedores pr ON p.proveedor_id = pr.id
WHERE p.stock < 10; -- Ajustar el límite según necesidad



-- Función para ventas por período
CREATE OR REPLACE FUNCTION reporte_ventas_periodo(
    fecha_inicio DATE, 
    fecha_fin DATE
)
RETURNS TABLE(
    fecha DATE,
    total_ventas DECIMAL,
    cantidad_ventas BIGINT,
    promedio_venta DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(v.fecha) as fecha,
        SUM(v.total) as total_ventas,
        COUNT(v.id) as cantidad_ventas,
        AVG(v.total) as promedio_venta
    FROM Ventas v
    WHERE DATE(v.fecha) BETWEEN fecha_inicio AND fecha_fin
    GROUP BY DATE(v.fecha)
    ORDER BY fecha;
END;
$$ LANGUAGE plpgsql;



-- Agregar campos de control temporal
ALTER TABLE Productos 
ADD COLUMN fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE Usuarios 
ADD COLUMN ultimo_login TIMESTAMP;

-- Tabla para roles de usuarios
CREATE TABLE Roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

ALTER TABLE Usuarios 
ADD COLUMN rol_id INT REFERENCES Roles(id);


-- Ventas del día actual
SELECT 
    v.id,
    v.fecha,
    u.nombre as vendedor,
    v.total,
    p.nombre as producto,
    dv.cantidad,
    dv.precio as precio_unitario
FROM Ventas v
JOIN Usuarios u ON v.usuario_id = u.id
JOIN Detalle_Ventas dv ON v.id = dv.venta_id
JOIN Productos p ON dv.producto_id = p.id
WHERE DATE(v.fecha) = CURRENT_DATE;

-- Productos más vendidos
SELECT 
    p.nombre,
    SUM(dv.cantidad) as total_vendido,
    SUM(dv.cantidad * dv.precio) as ingresos_totales
FROM Productos p
JOIN Detalle_Ventas dv ON p.id = dv.producto_id
GROUP BY p.id, p.nombre
ORDER BY total_vendido DESC
LIMIT 10;