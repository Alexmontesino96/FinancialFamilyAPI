-- Script para añadir el campo status a los pagos en PostgreSQL
-- Para ejecutar directamente en la base de datos:
-- financialfamilydb en render.com

-- 1. Crear el tipo enum si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paymentstatus') THEN
        CREATE TYPE paymentstatus AS ENUM ('PENDING', 'CONFIRM', 'INACTIVE');
        RAISE NOTICE 'Tipo enum paymentstatus creado exitosamente';
    ELSE
        RAISE NOTICE 'El tipo enum paymentstatus ya existe';
    END IF;
END;
$$;

-- 2. Añadir la columna status a la tabla payments si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name = 'status'
    ) THEN
        -- Añadir columna con valor predeterminado CONFIRM
        ALTER TABLE payments ADD COLUMN status paymentstatus DEFAULT 'CONFIRM'::paymentstatus;
        RAISE NOTICE 'Columna status añadida a la tabla payments';
    ELSE
        RAISE NOTICE 'La columna status ya existe en la tabla payments';
    END IF;
END;
$$;

-- 3. Actualizar los pagos existentes sin estado a CONFIRM
UPDATE payments SET status = 'CONFIRM'::paymentstatus WHERE status IS NULL;

-- 4. Verificar el resultado
SELECT 
    status,
    COUNT(*) as count
FROM payments
GROUP BY status
ORDER BY status; 