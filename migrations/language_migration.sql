-- Crear el tipo ENUM para language si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'language') THEN
        CREATE TYPE language AS ENUM ('EN', 'ES', 'FR');
    END IF;
END
$$;

-- Añadir la columna language a la tabla members con valor por defecto 'EN'
ALTER TABLE members ADD COLUMN IF NOT EXISTS language language NOT NULL DEFAULT 'EN';

-- Crear una versión de Alembic para registrar este cambio
INSERT INTO alembic_version (version_num) VALUES ('912a1d143c89')
ON CONFLICT (version_num) DO NOTHING; 