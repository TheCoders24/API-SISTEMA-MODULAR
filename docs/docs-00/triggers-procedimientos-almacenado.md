CREATE OR REPLACE FUNCTION fn_auditoria_productos()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO auditoria(tabla_afectada, accion, id_registro, detalles, usuario_nombre)
        VALUES ('productos', 'INSERT', NEW.id, 
                'Nuevo producto: ' || NEW.nombre, current_user);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO auditoria(tabla_afectada, accion, id_registro, detalles, usuario_nombre)
        VALUES ('productos', 'UPDATE', NEW.id, 
                'Producto modificado. Antes: ' || OLD.nombre || ', Ahora: ' || NEW.nombre, current_user);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO auditoria(tabla_afectada, accion, id_registro, detalles, usuario_nombre)
        VALUES ('productos', 'DELETE', OLD.id, 
                'Producto eliminado: ' || OLD.nombre, current_user);
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_auditoria_productos
AFTER INSERT OR UPDATE OR DELETE ON productos
FOR EACH ROW
EXECUTE FUNCTION fn_auditoria_productos();


-- Funciones y triggers

CREATE OR REPLACE FUNCTION actualizar_stock() RETURNS TRIGGER AS $$ 
BEGIN
    IF NEW.tipo = 'entrada' THEN 
        UPDATE Productos SET stock = stock + NEW.cantidad WHERE id = NEW.producto_id; 
    ELSIF NEW.tipo = 'salida' THEN 
        UPDATE Productos SET stock = stock - NEW.cantidad WHERE id = NEW.producto_id; 
    END IF; 
    RETURN NEW; 
END; 
$$ LANGUAGE plpgsql;

-- Función trigger registrar_auditoria actualizada: usuario_id se elimina, solo usuario_nombre NULL
CREATE OR REPLACE FUNCTION registrar_auditoria() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO Auditoria (tabla_afectada, accion, id_registro, usuario_nombre, detalles)
        VALUES (TG_TABLE_NAME, 'INSERT', NEW.id, NULL, row_to_json(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO Auditoria (tabla_afectada, accion, id_registro, usuario_nombre, detalles)
        VALUES (TG_TABLE_NAME, 'UPDATE', NEW.id, NULL, row_to_json(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO Auditoria (tabla_afectada, accion, id_registro, usuario_nombre, detalles)
        VALUES (TG_TABLE_NAME, 'DELETE', OLD.id, NULL, row_to_json(OLD));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Función trigger registrar_cambio_precio actualizada: usuario_id NULL
CREATE OR REPLACE FUNCTION registrar_cambio_precio() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.precio IS DISTINCT FROM NEW.precio THEN
        INSERT INTO Historial_Precios (producto_id, precio_anterior, precio_nuevo, usuario_id)
        VALUES (NEW.id, OLD.precio, NEW.precio, NULL);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER trg_actualizar_stock 
AFTER INSERT ON Movimientos 
FOR EACH ROW 
EXECUTE FUNCTION actualizar_stock();

CREATE TRIGGER trg_auditoria_usuarios 
AFTER INSERT OR UPDATE OR DELETE ON Usuarios 
FOR EACH ROW 
EXECUTE FUNCTION registrar_auditoria();

CREATE TRIGGER trg_auditoria_productos 
AFTER INSERT OR UPDATE OR DELETE ON Productos 
FOR EACH ROW 
EXECUTE FUNCTION registrar_auditoria();

CREATE TRIGGER trg_auditoria_movimientos 
AFTER INSERT OR UPDATE OR DELETE ON Movimientos 
FOR EACH ROW 
EXECUTE FUNCTION registrar_auditoria();

CREATE TRIGGER trg_cambio_precio 
AFTER UPDATE ON Productos 
FOR EACH ROW 
EXECUTE FUNCTION registrar_cambio_precio();

-- Vistas y funciones complejas

CREATE VIEW Reporte_Ventas AS
SELECT 
    V.id AS venta_id,
    V.fecha,
    V.total,
    U.nombre AS usuario,
    JSON_AGG(
        JSON_BUILD_OBJECT(
            'producto', P.nombre,
            'cantidad', DV.cantidad,
            'precio', DV.precio
        )
    ) AS productos
FROM Ventas V
JOIN Usuarios U ON V.usuario_id = U.id
JOIN Detalle_Ventas DV ON V.id = DV.venta_id
JOIN Productos P ON DV.producto_id = P.id
GROUP BY V.id, V.fecha, V.total, U.nombre;

CREATE OR REPLACE FUNCTION realizar_venta(
    p_usuario_id INT,
    p_productos JSON
) RETURNS INT AS $$
DECLARE
    v_venta_id INT;
    v_total DECIMAL(10, 2) := 0;
    v_producto JSON;
BEGIN
    INSERT INTO Ventas (total, usuario_id) VALUES (0, p_usuario_id)
    RETURNING id INTO v_venta_id;

    FOR v_producto IN SELECT * FROM json_array_elements(p_productos) LOOP
        INSERT INTO Detalle_Ventas (venta_id, producto_id, cantidad, precio)
        VALUES (
            v_venta_id,
            (v_producto->>'producto_id')::INT,
            (v_producto->>'cantidad')::INT,
            (SELECT precio FROM Productos WHERE id = (v_producto->>'producto_id')::INT)
        );

        v_total := v_total + ((v_producto->>'cantidad')::INT * 
                    (SELECT precio FROM Productos WHERE id = (v_producto->>'producto_id')::INT));

        UPDATE Productos 
        SET stock = stock - (v_producto->>'cantidad')::INT
        WHERE id = (v_producto->>'producto_id')::INT;
    END LOOP;

    UPDATE Ventas SET total = v_total WHERE id = v_venta_id;
    RETURN v_venta_id;
END;
$$ LANGUAGE plpgsql;

-- Datos iniciales y comentarios
INSERT INTO Configuraciones (clave, valor, descripcion)
VALUES 
    ('IVA', '16', 'Impuesto al Valor Agregado'),
    ('MONEDA', 'USD', 'Moneda predeterminada del sistema');

COMMENT ON TABLE Usuarios IS 'Tabla que almacena la información de los usuarios del sistema.';
COMMENT ON COLUMN Usuarios.password IS 'Contraseña encriptada del usuario.';




#  correcion despues de ejecutar toda la base de datos ejecutar lo siguiente para hacer correciones de un trigger de registrar_auditoria

CREATE OR REPLACE FUNCTION registrar_auditoria() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO Auditoria (tabla_afectada, accion, id_registro, usuario_id, detalles)
        VALUES (TG_TABLE_NAME, 'INSERT', NEW.id, NULL, row_to_json(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO Auditoria (tabla_afectada, accion, id_registro, usuario_id, detalles)
        VALUES (TG_TABLE_NAME, 'UPDATE', NEW.id, NULL, row_to_json(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO Auditoria (tabla_afectada, accion, id_registro, usuario_id, detalles)
        VALUES (TG_TABLE_NAME, 'DELETE', OLD.id, NULL, row_to_json(OLD));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

# correciones y cambios en lo siguiente:
# Función de cambio de precio

CREATE OR REPLACE FUNCTION registrar_cambio_precio() RETURNS TRIGGER AS $$
BEGIN
    IF OLD.precio IS DISTINCT FROM NEW.precio THEN
        INSERT INTO Historial_Precios (producto_id, precio_anterior, precio_nuevo, usuario_id)
        VALUES (NEW.id, OLD.precio, NEW.precio, NULL);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- 2. Crear función de auditoría
CREATE OR REPLACE FUNCTION auditoria_delete()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO auditoria (id_registro, tabla, accion, fecha)
    VALUES (OLD.id, TG_TABLE_NAME, 'DELETE', now());
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- 3. Crear trigger para la tabla productos
CREATE TRIGGER trg_auditoria_delete
AFTER DELETE ON productos
FOR EACH ROW
EXECUTE FUNCTION auditoria_delete();