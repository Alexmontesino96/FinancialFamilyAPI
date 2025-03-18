-- Script para añadir la columna status a la tabla payments
-- Primero comprobamos si la columna ya existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'payments' AND column_name = 'status'
    ) THEN
        -- Crear el tipo enum si no existe
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paymentstatus') THEN
            CREATE TYPE paymentstatus AS ENUM ('PENDING', 'CONFIRM', 'INACTIVE');
        END IF;
        
        -- Añadir la columna status con valor por defecto CONFIRM
        ALTER TABLE payments ADD COLUMN status paymentstatus DEFAULT 'CONFIRM'::paymentstatus;
        
        -- Actualizar los pagos existentes (por si acaso)
        UPDATE payments SET status = 'CONFIRM'::paymentstatus WHERE status IS NULL;
        
        RAISE NOTICE 'Columna status añadida a la tabla payments';
    ELSE
        RAISE NOTICE 'La columna status ya existe en la tabla payments';
    END IF;
END;
$$; 