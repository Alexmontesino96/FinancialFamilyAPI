-- Crear el tipo ENUM para payment_status si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status') THEN
        CREATE TYPE payment_status AS ENUM ('PENDING', 'CONFIRM', 'INACTIVE');
    END IF;
END
$$;

-- Añadir la columna status a la tabla payments con valor por defecto 'PENDING'
ALTER TABLE payments ADD COLUMN IF NOT EXISTS status payment_status NOT NULL DEFAULT 'PENDING';

-- Crear un índice para mejorar el rendimiento de las consultas por status
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

-- Informar resultado
SELECT 'Columna "status" añadida a la tabla "payments" con éxito' AS resultado; 