"""
Script para limpiar la base de datos

Este script elimina todos los datos de la base de datos, incluyendo:
- Todos los pagos
- Todos los gastos
- Todos los miembros
- Todas las familias

Es útil para comenzar con una base de datos limpia durante el desarrollo.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener la URL de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: No se ha configurado la variable de entorno DATABASE_URL")
    sys.exit(1)

# Crear conexión a la base de datos
print(f"Conectando a la base de datos...")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def clean_database():
    """Elimina todos los datos de la base de datos."""
    db = SessionLocal()
    try:
        # Verificar la conexión a la base de datos
        try:
            db.execute(text("SELECT 1"))
            print("Conexión exitosa a la base de datos")
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            return False
        
        # Contar entidades antes de eliminar
        payments_count = db.execute(text("SELECT COUNT(*) FROM payments")).scalar()
        expenses_count = db.execute(text("SELECT COUNT(*) FROM expenses")).scalar()
        members_count = db.execute(text("SELECT COUNT(*) FROM members")).scalar()
        families_count = db.execute(text("SELECT COUNT(*) FROM families")).scalar()
        
        print(f"\nEntidades encontradas:")
        print(f"- Pagos: {payments_count}")
        print(f"- Gastos: {expenses_count}")
        print(f"- Miembros: {members_count}")
        print(f"- Familias: {families_count}")
        
        if payments_count == 0 and expenses_count == 0 and members_count == 0 and families_count == 0:
            print("\nLa base de datos ya está vacía, no hay nada que eliminar.")
            return True
        
        # Pedir confirmación
        confirmation = input("\n¡ADVERTENCIA! Esta operación eliminará TODOS los datos de la base de datos. ¿Estás seguro? (s/N): ")
        if confirmation.lower() != 's':
            print("Operación cancelada por el usuario.")
            return False
        
        # Desactivar restricciones de clave foránea temporalmente para PostgreSQL
        db.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        
        print("\nEliminando datos...")
        
        # Limpiar la tabla de asociación expense_member
        db.execute(text("DELETE FROM expense_member_association"))
        print("- Asociaciones de gastos y miembros eliminadas")
        
        # Eliminar pagos
        db.execute(text("DELETE FROM payments"))
        print("- Pagos eliminados")
        
        # Eliminar gastos
        db.execute(text("DELETE FROM expenses"))
        print("- Gastos eliminados")
        
        # Eliminar miembros
        db.execute(text("DELETE FROM members"))
        print("- Miembros eliminados")
        
        # Eliminar familias
        db.execute(text("DELETE FROM families"))
        print("- Familias eliminadas")
        
        # Aplicar los cambios
        db.commit()
        
        # Verificar que se han eliminado todos los datos
        payments_count = db.execute(text("SELECT COUNT(*) FROM payments")).scalar()
        expenses_count = db.execute(text("SELECT COUNT(*) FROM expenses")).scalar()
        members_count = db.execute(text("SELECT COUNT(*) FROM members")).scalar()
        families_count = db.execute(text("SELECT COUNT(*) FROM families")).scalar()
        
        print("\nVerificación final:")
        print(f"- Pagos: {payments_count}")
        print(f"- Gastos: {expenses_count}")
        print(f"- Miembros: {members_count}")
        print(f"- Familias: {families_count}")
        
        if payments_count == 0 and expenses_count == 0 and members_count == 0 and families_count == 0:
            print("\n¡Base de datos limpiada exitosamente!")
            return True
        else:
            print("\nAdvertencia: No se pudieron eliminar todos los datos.")
            return False
    
    except Exception as e:
        db.rollback()
        print(f"\nError durante la limpieza de la base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=== LIMPIEZA DE BASE DE DATOS ===")
    clean_database() 