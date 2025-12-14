
### **Mejoras Implementadas:**
- ✅ Índices para optimización
- ✅ Triggers para automatización de stock
- ✅ Vistas para reportes
- ✅ Funciones almacenadas
- ✅ Campos de control temporal
- ✅ Sistema de roles de usuarios

## 🔧 **Mejoras Adicionales Recomendadas**

### 1. **Triggers para Auditoría Automática**
```sql
-- Función para auditoría automática
CREATE OR REPLACE FUNCTION registrar_auditoria()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO Auditoria (tabla_afectada, accion, id_registro, detalles)
        VALUES (TG_TABLE_NAME, 'DELETE', OLD.id, row_to_json(OLD)::TEXT);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO Auditoria (tabla_afectada, accion, id_registro, detalles)
        VALUES (TG_TABLE_NAME, 'UPDATE', NEW.id, 
                'ANTIGUO: ' || row_to_json(OLD)::TEXT || ' NUEVO: ' || row_to_json(NEW)::TEXT);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO Auditoria (tabla_afectada, accion, id_registro, detalles)
        VALUES (TG_TABLE_NAME, 'INSERT', NEW.id, row_to_json(NEW)::TEXT);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Aplicar a tablas críticas
CREATE TRIGGER tr_auditoria_productos
    AFTER INSERT OR UPDATE OR DELETE ON Productos
    FOR EACH ROW EXECUTE FUNCTION registrar_auditoria();

CREATE TRIGGER tr_auditoria_ventas
    AFTER INSERT OR UPDATE OR DELETE ON Ventas
    FOR EACH ROW EXECUTE FUNCTION registrar_auditoria();

CREATE TRIGGER tr_auditoria_usuarios
    AFTER INSERT OR UPDATE OR DELETE ON Usuarios
    FOR EACH ROW EXECUTE FUNCTION registrar_auditoria();
```

### 2. **Trigger para Actualizar Fecha de Modificación**
```sql
CREATE OR REPLACE FUNCTION actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_actualizar_productos
    BEFORE UPDATE ON Productos
    FOR EACH ROW EXECUTE FUNCTION actualizar_timestamp();
```

### 3. **Función para Realizar Ventas con Validación**
```sql
CREATE OR REPLACE FUNCTION realizar_venta(
    p_usuario_id INT,
    p_detalles JSONB
)
RETURNS INT AS $$
DECLARE
    v_venta_id INT;
    v_total DECIMAL(10,2) := 0;
    detalle RECORD;
BEGIN
    -- Validar stock antes de proceder
    FOR detalle IN 
        SELECT (value->>'producto_id')::INT as producto_id, 
               (value->>'cantidad')::INT as cantidad
        FROM jsonb_array_elements(p_detalles)
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM Productos 
            WHERE id = detalle.producto_id AND stock >= detalle.cantidad
        ) THEN
            RAISE EXCEPTION 'Stock insuficiente para el producto ID: %', detalle.producto_id;
        END IF;
    END LOOP;

    -- Crear la venta
    INSERT INTO Ventas (usuario_id, total) 
    VALUES (p_usuario_id, 0)
    RETURNING id INTO v_venta_id;

    -- Insertar detalles y calcular total
    INSERT INTO Detalle_Ventas (venta_id, producto_id, cantidad, precio)
    SELECT 
        v_venta_id,
        (value->>'producto_id')::INT,
        (value->>'cantidad')::INT,
        (SELECT precio FROM Productos WHERE id = (value->>'producto_id')::INT)
    FROM jsonb_array_elements(p_detalles);

    -- Calcular total actualizado
    SELECT SUM(dv.cantidad * dv.precio) INTO v_total
    FROM Detalle_Ventas dv
    WHERE dv.venta_id = v_venta_id;

    -- Actualizar total de la venta
    UPDATE Ventas SET total = v_total WHERE id = v_venta_id;

    RETURN v_venta_id;
END;
$$ LANGUAGE plpgsql;
```

### 4. **Vistas Adicionales Útiles**
```sql
-- Vista para historial completo de movimientos
CREATE VIEW vista_movimientos_completo AS
SELECT 
    m.fecha,
    p.nombre as producto,
    c.nombre as categoria,
    m.tipo,
    m.cantidad,
    u.nombre as usuario,
    CASE 
        WHEN m.tipo = 'entrada' THEN '+'
        WHEN m.tipo = 'salida' THEN '-'
    END as simbolo
FROM Movimientos m
JOIN Productos p ON m.producto_id = p.id
LEFT JOIN Categorias c ON p.categoria_id = c.id
LEFT JOIN Usuarios u ON m.usuario_id = u.id
ORDER BY m.fecha DESC;

-- Vista para análisis de proveedores
CREATE VIEW vista_analisis_proveedores AS
SELECT 
    pr.id,
    pr.nombre as proveedor,
    COUNT(DISTINCT pp.id) as total_pedidos,
    SUM(pp.total) as total_comprado,
    COUNT(DISTINCT p.id) as productos_suministrados,
    AVG(dpp.precio) as precio_promedio
FROM Proveedores pr
LEFT JOIN Pedidos_Proveedores pp ON pr.id = pp.proveedor_id
LEFT JOIN Detalle_Pedidos_Proveedores dpp ON pp.id = dpp.pedido_id
LEFT JOIN Productos p ON pr.id = p.proveedor_id
GROUP BY pr.id, pr.nombre;
```

### 5. **Consultas de Ejemplo para el Sistema**
```sql
-- Dashboard principal - Métricas clave
SELECT 
    (SELECT COUNT(*) FROM Productos WHERE stock < 10) as productos_stock_bajo,
    (SELECT SUM(total) FROM Ventas WHERE DATE(fecha) = CURRENT_DATE) as ventas_hoy,
    (SELECT COUNT(*) FROM Ventas WHERE DATE(fecha) = CURRENT_DATE) as transacciones_hoy,
    (SELECT SUM(stock * precio) FROM Productos) as valor_inventario;

-- Análisis de tendencias de ventas
SELECT 
    EXTRACT(MONTH FROM fecha) as mes,
    EXTRACT(YEAR FROM fecha) as año,
    COUNT(*) as ventas_totales,
    SUM(total) as ingresos_totales,
    AVG(total) as ticket_promedio
FROM Ventas
GROUP BY EXTRACT(YEAR FROM fecha), EXTRACT(MONTH FROM fecha)
ORDER BY año, mes;

-- Rotación de inventario
SELECT 
    p.nombre,
    p.stock,
    COALESCE(SUM(dv.cantidad), 0) as vendidos_mes,
    CASE 
        WHEN p.stock > 0 THEN COALESCE(SUM(dv.cantidad), 0) / p.stock 
        ELSE 0 
    END as ratio_rotacion
FROM Productos p
LEFT JOIN Detalle_Ventas dv ON p.id = dv.producto_id
LEFT JOIN Ventas v ON dv.venta_id = v.id
WHERE v.fecha >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY p.id, p.nombre, p.stock
ORDER BY ratio_rotacion DESC;
```

### 6. **Configuración de Roles Básicos**
```sql
-- Insertar roles básicos
INSERT INTO Roles (nombre, descripcion) VALUES 
('admin', 'Administrador completo del sistema'),
('vendedor', 'Puede realizar ventas y consultar reportes'),
('inventario', 'Gestiona productos y proveedores');

-- Asignar rol por defecto a usuarios existentes
UPDATE Usuarios SET rol_id = (SELECT id FROM Roles WHERE nombre = 'vendedor') 
WHERE rol_id IS NULL;
```
