"""
Script de migración para añadir el campo status a los pagos existentes

Este script actualiza todos los pagos existentes en la base de datos
estableciendo su estado como CONFIRM, ya que anteriormente todos los pagos
se consideraban confirmados automáticamente.

Utiliza la conexión directa a PostgreSQL para realizar la migración.
"""

import sys
import os
from sqlalchemy import create_engine, text, Column, Enum
from sqlalchemy.orm import sessionmaker, Session
import enum
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conexión directa a la base de datos PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set in environment variables. This is required for database connection.")
    
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Definir el enum PaymentStatus para verificación
class PaymentStatus(enum.Enum):
    """
    Enum para los valores de estado de pago.
    
    Attributes:
        PENDING: Pago creado pero no confirmado por el receptor
        CONFIRM: Pago confirmado por el receptor
        INACTIVE: Pago rechazado o cancelado
    """
    PENDING = "PENDING"
    CONFIRM = "CONFIRM"
    INACTIVE = "INACTIVE"

def get_db():
    """Obtener una sesión de base de datos para la migración."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_column_exists(db, table, column):
    """
    Verifica si una columna existe en una tabla.
    
    Args:
        db (Session): Sesión de base de datos
        table (str): Nombre de la tabla
        column (str): Nombre de la columna
        
    Returns:
        bool: True si la columna existe, False en caso contrario
    """
    result = db.execute(
        text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{column}'")
    ).fetchone()
    return result is not None

def check_enum_exists(db, enum_name):
    """
    Verifica si un tipo enum existe en la base de datos.
    
    Args:
        db (Session): Sesión de base de datos
        enum_name (str): Nombre del tipo enum
        
    Returns:
        bool: True si el enum existe, False en caso contrario
    """
    result = db.execute(
        text(f"SELECT 1 FROM pg_type WHERE typname = '{enum_name}'")
    ).fetchone()
    return result is not None

def create_enum_type(db):
    """
    Crea el tipo enum para PaymentStatus si no existe.
    
    Args:
        db (Session): Sesión de base de datos
        
    Returns:
        bool: True si se creó el enum, False si ya existía
    """
    if not check_enum_exists(db, 'paymentstatus'):
        print("Creando tipo enum 'paymentstatus'...")
        db.execute(text("""
            CREATE TYPE paymentstatus AS ENUM ('PENDING', 'CONFIRM', 'INACTIVE')
        """))
        db.commit()
        return True
    else:
        print("El tipo enum 'paymentstatus' ya existe")
        return False

def add_status_column(db):
    """
    Añade la columna status a la tabla payments si no existe.
    
    Args:
        db (Session): Sesión de base de datos
    
    Returns:
        bool: True si se añadió la columna, False si ya existía
    """
    if not check_column_exists(db, 'payments', 'status'):
        print("La columna 'status' no existe en la tabla 'payments'")
        
        # Asegurar que existe el tipo enum
        create_enum_type(db)
        
        # Añadir la columna status con valor por defecto CONFIRM
        print("Añadiendo columna 'status' a la tabla 'payments'...")
        db.execute(text("""
            ALTER TABLE payments ADD COLUMN status paymentstatus DEFAULT 'CONFIRM'::paymentstatus
        """))
        
        db.commit()
        print("Columna 'status' añadida exitosamente")
        return True
    else:
        print("La columna 'status' ya existe en la tabla 'payments'")
        return False

def update_existing_payments(db):
    """
    Actualiza todos los pagos existentes sin estado a CONFIRM.
    
    Args:
        db (Session): Sesión de base de datos
        
    Returns:
        int: Número de filas actualizadas
    """
    print("Actualizando pagos existentes sin estado...")
    result = db.execute(text("""
        UPDATE payments SET status = 'CONFIRM'::paymentstatus 
        WHERE status IS NULL
    """))
    db.commit()
    
    # Obtener el número de filas afectadas (puede no funcionar en todas las implementaciones)
    rows_affected = getattr(result, 'rowcount', None)
    if rows_affected is not None:
        print(f"Se actualizaron {rows_affected} pagos a estado CONFIRM")
        return rows_affected
    else:
        print("Pagos actualizados (número desconocido)")
        return 0

def migrate_payment_status():
    """
    Ejecuta la migración completa:
    1. Crea el tipo enum si no existe
    2. Añade la columna status si no existe
    3. Actualiza todos los pagos existentes sin estado
    
    Returns:
        bool: True si la migración fue exitosa
    """
    print("\n=== INICIANDO MIGRACIÓN DE ESTADO DE PAGOS ===")
    
    db = next(get_db())
    try:
        # Paso 1: Crear/verificar el enum
        enum_created = create_enum_type(db)
        
        # Paso 2: Añadir la columna status
        column_added = add_status_column(db)
        
        # Paso 3: Actualizar los pagos existentes
        rows_updated = update_existing_payments(db)
        
        print("\n✅ Migración completada exitosamente")
        print(f"  - Enum creado: {'Sí' if enum_created else 'No (ya existía)'}")
        print(f"  - Columna añadida: {'Sí' if column_added else 'No (ya existía)'}")
        print(f"  - Pagos actualizados: {rows_updated}")
        
        return True
    
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error durante la migración: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    try:
        success = migrate_payment_status()
        if success:
            print("\n=== MIGRACIÓN FINALIZADA CORRECTAMENTE ===")
        else:
            print("\n=== MIGRACIÓN FINALIZADA CON ERRORES ===")
    except Exception as e:
        print(f"\n❌ ERROR NO CONTROLADO: {e}")
        import traceback
        traceback.print_exc() 