BEGIN;

-- =============================
-- TABLAS BASE
-- =============================
CREATE TABLE IF NOT EXISTS public.roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS public.categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS public.proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    contacto VARCHAR(100),
    telefono VARCHAR(20) CHECK (telefono ~ '^[0-9]{10}$'),
    email VARCHAR(100) CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')
);

CREATE TABLE IF NOT EXISTS public.usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(512) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================
-- TABLAS DEPENDIENTES
-- =============================
CREATE TABLE IF NOT EXISTS public.productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0),
    stock INT NOT NULL CHECK (stock >= 0),
    categoria_id INT REFERENCES public.categorias(id) ON DELETE SET NULL,
    proveedor_id INT REFERENCES public.proveedores(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.ventas (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total NUMERIC(10, 2) NOT NULL CHECK (total >= 0),
    usuario_id INT REFERENCES public.usuarios(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.movimientos (
    id SERIAL PRIMARY KEY,
    producto_id INT NOT NULL REFERENCES public.productos(id) ON DELETE CASCADE,
    tipo VARCHAR(20) CHECK (tipo IN ('entrada', 'salida', 'ajuste')) NOT NULL,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT REFERENCES public.usuarios(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.pedidos_proveedores (
    id SERIAL PRIMARY KEY,
    proveedor_id INT NOT NULL REFERENCES public.proveedores(id) ON DELETE CASCADE,
    fecha_pedido TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP WITH TIME ZONE,
    total NUMERIC(10, 2) NOT NULL CHECK (total >= 0)
);

-- =============================
-- TABLAS DE RELACIÓN
-- =============================
CREATE TABLE IF NOT EXISTS public.usuarios_roles (
    usuario_id INT REFERENCES public.usuarios(id) ON DELETE CASCADE,
    rol_id INT REFERENCES public.roles(id) ON DELETE CASCADE,
    PRIMARY KEY (usuario_id, rol_id)
);

CREATE TABLE IF NOT EXISTS public.detalle_ventas (
    id SERIAL PRIMARY KEY,
    venta_id INT NOT NULL REFERENCES public.ventas(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES public.productos(id) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0)
);

CREATE TABLE IF NOT EXISTS public.devoluciones (
    id SERIAL PRIMARY KEY,
    venta_id INT NOT NULL REFERENCES public.ventas(id) ON DELETE CASCADE,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    motivo TEXT,
    usuario_id INT REFERENCES public.usuarios(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.detalle_devoluciones (
    id SERIAL PRIMARY KEY,
    devolucion_id INT NOT NULL REFERENCES public.devoluciones(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES public.productos(id) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0)
);

CREATE TABLE IF NOT EXISTS public.detalle_pedidos_proveedores (
    id SERIAL PRIMARY KEY,
    pedido_id INT NOT NULL REFERENCES public.pedidos_proveedores(id) ON DELETE CASCADE,
    producto_id INT NOT NULL REFERENCES public.productos(id) ON DELETE CASCADE,
    cantidad INT NOT NULL CHECK (cantidad > 0),
    precio NUMERIC(10, 2) NOT NULL CHECK (precio >= 0)
);

-- =============================
-- TABLAS DE AUDITORÍA Y LOGS
-- =============================
CREATE TABLE IF NOT EXISTS public.metricas (
    id SERIAL PRIMARY KEY,
    tipo_metrica VARCHAR(50) NOT NULL,
    valor TEXT NOT NULL,
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.registroactividad (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    ip VARCHAR(45) NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accion VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.sesiones (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES public.usuarios(id) ON DELETE CASCADE,
    token VARCHAR(512) NOT NULL,
    fecha_inicio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP WITH TIME ZONE,
    activa BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS public.auditoria (
    id SERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(100) NOT NULL,
    accion VARCHAR(20) NOT NULL CHECK (accion IN ('INSERT', 'UPDATE', 'DELETE')),
    id_registro INT NOT NULL,
    usuario_nombre VARCHAR(100),
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    detalles TEXT
);

CREATE TABLE IF NOT EXISTS public.configuraciones (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(100) NOT NULL UNIQUE,
    valor TEXT NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS public.historial_precios (
    id SERIAL PRIMARY KEY,
    producto_id INT NOT NULL REFERENCES public.productos(id) ON DELETE CASCADE,
    precio_anterior NUMERIC(10, 2) NOT NULL,
    precio_nuevo NUMERIC(10, 2) NOT NULL,
    fecha_cambio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT REFERENCES public.usuarios(id) ON DELETE SET NULL
);

-- =============================
-- ÍNDICES
-- =============================
CREATE INDEX IF NOT EXISTS idx_productos_nombre ON public.productos(nombre);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON public.usuarios(email);
CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON public.movimientos(fecha);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON public.ventas(fecha);

-- =============================
-- FUNCIONES Y TRIGGERS
-- =============================
CREATE OR REPLACE FUNCTION actualizar_stock() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tipo = 'entrada' THEN
        UPDATE public.productos SET stock = stock + NEW.cantidad WHERE id = NEW.producto_id;
    ELSIF NEW.tipo = 'salida' THEN
        UPDATE public.productos SET stock = stock - NEW.cantidad WHERE id = NEW.producto_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION registrar_auditoria() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO public.auditoria (tabla_afectada, accion, id_registro, usuario_nombre, detalles)
        VALUES (TG_TABLE_NAME, 'INSERT', NEW.id, NULL, row_to_json(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO public.auditoria (tabla_afectada, accion, id_registro, usuario_nombre, detalles)
        VALUES (TG_TABLE_NAME, 'UPDATE', NEW.id, NULL, row_to_json(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO public.auditoria (tabla_afectada, accion, id_registro, usuario_nombre, detalles)
        VALUES (TG_TABLE_NAME, 'DELETE', OLD.id, NULL, row_to_json(OLD));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION registrar_cambio_precio() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.precio IS DISTINCT FROM NEW.precio THEN
        INSERT INTO public.historial_precios (producto_id, precio_anterior, precio_nuevo, usuario_id)
        VALUES (NEW.id, OLD.precio, NEW.precio, NULL);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION auditoria_delete() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.auditoria (tabla_afectada, accion, id_registro, fecha)
    VALUES (TG_TABLE_NAME, 'DELETE', OLD.id, now());
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_actualizar_stock
AFTER INSERT ON public.movimientos
FOR EACH ROW EXECUTE FUNCTION actualizar_stock();

CREATE TRIGGER trg_auditoria_usuarios
AFTER INSERT OR UPDATE OR DELETE ON public.usuarios
FOR EACH ROW EXECUTE FUNCTION registrar_auditoria();

CREATE TRIGGER trg_auditoria_productos
AFTER INSERT OR UPDATE OR DELETE ON public.productos
FOR EACH ROW EXECUTE FUNCTION registrar_auditoria();

CREATE TRIGGER trg_auditoria_movimientos
AFTER INSERT OR UPDATE OR DELETE ON public.movimientos
FOR EACH ROW EXECUTE FUNCTION registrar_auditoria();

CREATE TRIGGER trg_auditoria_delete
AFTER DELETE ON public.productos
FOR EACH ROW EXECUTE FUNCTION auditoria_delete();

CREATE TRIGGER trg_cambio_precio
AFTER UPDATE ON public.productos
FOR EACH ROW EXECUTE FUNCTION registrar_cambio_precio();

-- =============================
-- DATOS INICIALES
-- =============================
INSERT INTO public.configuraciones (clave, valor, descripcion) VALUES
    ('IVA', '16', 'Impuesto al Valor Agregado') ON CONFLICT (clave) DO NOTHING,
    ('MONEDA', 'USD', 'Moneda predeterminada del sistema') ON CONFLICT (clave) DO NOTHING;

COMMENT ON TABLE public.usuarios IS 'Tabla que almacena la información de los usuarios del sistema.';
COMMENT ON COLUMN public.usuarios.password IS 'Contraseña encriptada del usuario.';

END;
