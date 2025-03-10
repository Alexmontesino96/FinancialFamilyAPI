import sys
import os
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SQLALCHEMY_DATABASE_URL

def generate_uuid():
    return str(uuid.uuid4())

def run_migration():
    """Ejecuta la migración para convertir los IDs de enteros a UUIDs."""
    print("Iniciando migración para convertir IDs a UUIDs...")
    
    # Crear conexión a la base de datos
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Crear tablas temporales con la nueva estructura
        print("Creando tablas temporales...")
        
        # Tabla temporal para familias
        db.execute(text("""
        CREATE TABLE families_temp (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Tabla temporal para miembros
        db.execute(text("""
        CREATE TABLE members_temp (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            telegram_id VARCHAR UNIQUE,
            family_id VARCHAR(36) REFERENCES families_temp(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Tabla temporal para gastos
        db.execute(text("""
        CREATE TABLE expenses_temp (
            id VARCHAR(36) PRIMARY KEY,
            description VARCHAR,
            amount FLOAT,
            paid_by INTEGER REFERENCES members_temp(id),
            family_id VARCHAR(36) REFERENCES families_temp(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Tabla temporal para pagos
        db.execute(text("""
        CREATE TABLE payments_temp (
            id VARCHAR(36) PRIMARY KEY,
            from_member_id INTEGER REFERENCES members_temp(id),
            to_member_id INTEGER REFERENCES members_temp(id),
            amount FLOAT,
            family_id VARCHAR(36) REFERENCES families_temp(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Tabla temporal para la asociación entre gastos y miembros
        db.execute(text("""
        CREATE TABLE expense_member_association_temp (
            expense_id VARCHAR(36) REFERENCES expenses_temp(id),
            member_id INTEGER REFERENCES members_temp(id),
            PRIMARY KEY (expense_id, member_id)
        )
        """))
        
        # 2. Migrar datos de las tablas originales a las temporales
        print("Migrando datos...")
        
        # Crear un mapeo de IDs antiguos a nuevos UUIDs para familias
        family_id_map = {}
        families = db.execute(text("SELECT id, name, created_at FROM families")).fetchall()
        
        for family in families:
            old_id = family[0]
            new_id = generate_uuid()
            family_id_map[old_id] = new_id
            
            db.execute(
                text("INSERT INTO families_temp (id, name, created_at) VALUES (:id, :name, :created_at)"),
                {"id": new_id, "name": family[1], "created_at": family[2]}
            )
        
        # Migrar miembros
        members = db.execute(text("SELECT id, name, telegram_id, family_id, created_at FROM members")).fetchall()
        
        for member in members:
            old_family_id = member[3]
            new_family_id = family_id_map.get(old_family_id)
            
            db.execute(
                text("INSERT INTO members_temp (id, name, telegram_id, family_id, created_at) VALUES (:id, :name, :telegram_id, :family_id, :created_at)"),
                {"id": member[0], "name": member[1], "telegram_id": member[2], "family_id": new_family_id, "created_at": member[4]}
            )
        
        # Crear un mapeo de IDs antiguos a nuevos UUIDs para gastos
        expense_id_map = {}
        expenses = db.execute(text("SELECT id, description, amount, paid_by, family_id, created_at FROM expenses")).fetchall()
        
        for expense in expenses:
            old_id = expense[0]
            old_family_id = expense[4]
            new_id = generate_uuid()
            new_family_id = family_id_map.get(old_family_id)
            
            expense_id_map[old_id] = new_id
            
            db.execute(
                text("INSERT INTO expenses_temp (id, description, amount, paid_by, family_id, created_at) VALUES (:id, :description, :amount, :paid_by, :family_id, :created_at)"),
                {"id": new_id, "description": expense[1], "amount": expense[2], "paid_by": expense[3], "family_id": new_family_id, "created_at": expense[5]}
            )
        
        # Migrar pagos
        payments = db.execute(text("SELECT id, from_member_id, to_member_id, amount, family_id, created_at FROM payments")).fetchall()
        
        for payment in payments:
            old_id = payment[0]
            old_family_id = payment[4]
            new_id = generate_uuid()
            new_family_id = family_id_map.get(old_family_id)
            
            db.execute(
                text("INSERT INTO payments_temp (id, from_member_id, to_member_id, amount, family_id, created_at) VALUES (:id, :from_member_id, :to_member_id, :amount, :family_id, :created_at)"),
                {"id": new_id, "from_member_id": payment[1], "to_member_id": payment[2], "amount": payment[3], "family_id": new_family_id, "created_at": payment[5]}
            )
        
        # Migrar asociaciones entre gastos y miembros
        associations = db.execute(text("SELECT expense_id, member_id FROM expense_member_association")).fetchall()
        
        for assoc in associations:
            old_expense_id = assoc[0]
            new_expense_id = expense_id_map.get(old_expense_id)
            
            db.execute(
                text("INSERT INTO expense_member_association_temp (expense_id, member_id) VALUES (:expense_id, :member_id)"),
                {"expense_id": new_expense_id, "member_id": assoc[1]}
            )
        
        # 3. Renombrar tablas
        print("Renombrando tablas...")
        
        # Eliminar las tablas originales (en orden inverso para respetar las restricciones de clave foránea)
        db.execute(text("DROP TABLE IF EXISTS expense_member_association"))
        db.execute(text("DROP TABLE IF EXISTS payments"))
        db.execute(text("DROP TABLE IF EXISTS expenses"))
        db.execute(text("DROP TABLE IF EXISTS members"))
        db.execute(text("DROP TABLE IF EXISTS families"))
        
        # Renombrar las tablas temporales
        db.execute(text("ALTER TABLE families_temp RENAME TO families"))
        db.execute(text("ALTER TABLE members_temp RENAME TO members"))
        db.execute(text("ALTER TABLE expenses_temp RENAME TO expenses"))
        db.execute(text("ALTER TABLE payments_temp RENAME TO payments"))
        db.execute(text("ALTER TABLE expense_member_association_temp RENAME TO expense_member_association"))
        
        # 4. Recrear índices
        print("Recreando índices...")
        
        db.execute(text("CREATE INDEX ix_families_id ON families(id)"))
        db.execute(text("CREATE INDEX ix_families_name ON families(name)"))
        db.execute(text("CREATE INDEX ix_members_id ON members(id)"))
        db.execute(text("CREATE INDEX ix_members_name ON members(name)"))
        db.execute(text("CREATE INDEX ix_members_telegram_id ON members(telegram_id)"))
        db.execute(text("CREATE INDEX ix_expenses_id ON expenses(id)"))
        db.execute(text("CREATE INDEX ix_expenses_description ON expenses(description)"))
        db.execute(text("CREATE INDEX ix_payments_id ON payments(id)"))
        
        # Confirmar los cambios
        db.commit()
        print("Migración completada con éxito.")
        
    except Exception as e:
        db.rollback()
        print(f"Error durante la migración: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run_migration() 