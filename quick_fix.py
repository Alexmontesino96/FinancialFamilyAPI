#!/usr/bin/env python3
"""
Script simple para aplicar las correcciones críticas.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Usar variables de entorno para la conexión
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.odwrhwpqynwtbvpigmbc:tuvpup-megba8-giwxAx@aws-0-us-west-1.pooler.supabase.com:5432/postgres")

def main():
    print("🚀 Aplicando correcciones críticas...")
    
    # Crear engine y sesión
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Eliminar duplicados existentes
        print("🧹 Eliminando duplicados en debt_cache...")
        result = db.execute(text("""
            DELETE FROM debt_cache a USING debt_cache b 
            WHERE a.id > b.id 
            AND a.family_id = b.family_id 
            AND a.from_member_id = b.from_member_id 
            AND a.to_member_id = b.to_member_id
        """))
        print(f"   Eliminados {result.rowcount} registros duplicados")
        
        # 2. Verificar si ya existe el constraint
        constraint_exists = db.execute(text("""
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'unique_debt_per_pair' 
            AND table_name = 'debt_cache'
        """)).fetchone()
        
        if not constraint_exists:
            print("🔐 Agregando constraint UNIQUE...")
            db.execute(text("""
                ALTER TABLE debt_cache 
                ADD CONSTRAINT unique_debt_per_pair 
                UNIQUE (family_id, from_member_id, to_member_id)
            """))
            print("   ✅ Constraint UNIQUE agregado")
        else:
            print("   ℹ️ Constraint UNIQUE ya existe")
        
        # 3. Verificar integridad
        print("🔍 Verificando integridad...")
        duplicates = db.execute(text("""
            SELECT family_id, from_member_id, to_member_id, COUNT(*) as count
            FROM debt_cache 
            GROUP BY family_id, from_member_id, to_member_id 
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if duplicates:
            print(f"   ⚠️ Aún hay {len(duplicates)} grupos de duplicados")
        else:
            print("   ✅ No hay duplicados")
        
        db.commit()
        print("🎉 ¡Correcciones aplicadas exitosamente!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()