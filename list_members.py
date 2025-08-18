#!/usr/bin/env python3
"""
Script para listar todos los miembros de la base de datos.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.odwrhwpqynwtbvpigmbc:tuvpup-megba8-giwxAx@aws-0-us-west-1.pooler.supabase.com:5432/postgres")

def main():
    engine = create_engine(DATABASE_URL) 
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("👥 Miembros en la base de datos:")
        print("=" * 50)
        
        members = db.execute(text("""
            SELECT m.id, m.name, f.name as family_name, m.family_id
            FROM members m
            JOIN families f ON m.family_id = f.id
            ORDER BY f.name, m.name
        """)).fetchall()
        
        current_family = None
        for member in members:
            if member.family_name != current_family:
                current_family = member.family_name
                print(f"\n🏠 Familia: {current_family}")
                print("-" * 30)
            
            print(f"   👤 {member.name} (ID: {member.id[:8]}...)")
        
        print(f"\n📊 Total: {len(members)} miembros")
        
        # También mostrar algunos balances recientes
        print("\n💰 Últimos balances en debt_cache:")
        print("=" * 50)
        
        debts = db.execute(text("""
            SELECT 
                dc.amount,
                m1.name as from_name,
                m2.name as to_name,
                dc.last_updated
            FROM debt_cache dc
            JOIN members m1 ON dc.from_member_id = m1.id
            JOIN members m2 ON dc.to_member_id = m2.id
            WHERE dc.amount > 0
            ORDER BY dc.last_updated DESC
            LIMIT 10
        """)).fetchall()
        
        for debt in debts:
            print(f"   {debt.from_name} debe ${debt.amount:.2f} a {debt.to_name}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()