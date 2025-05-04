"""
Script para crear las tablas de caché de balances en la base de datos.

Este script crea las tablas necesarias para el sistema de caché de balances:
1. member_balance_cache: Almacena los balances generales de cada miembro
2. debt_cache: Almacena las deudas específicas entre miembros
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import MetaData, Table, Column, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.database import engine
from app.utils.logging_config import get_logger

# Usar nuestro sistema de logging centralizado
logger = get_logger("balance_cache_tables")

def create_balance_cache_tables():
    """
    Crea las tablas de caché de balances en la base de datos.
    """
    logger.info("Creando tablas de caché de balances...")
    
    try:
        metadata = MetaData()
        
        # Tabla para caché de balances de miembros
        member_balance_cache = Table(
            'member_balance_cache', 
            metadata,
            Column('id', String(36), primary_key=True),
            Column('member_id', String(36), ForeignKey('members.id'), index=True),
            Column('family_id', String(36), ForeignKey('families.id'), index=True),
            Column('total_debt', Float, default=0.0),
            Column('total_owed', Float, default=0.0),
            Column('net_balance', Float, default=0.0),
            Column('last_updated', DateTime(timezone=True), server_default=func.now())
        )
        
        # Tabla para caché de deudas específicas
        debt_cache = Table(
            'debt_cache', 
            metadata,
            Column('id', String(36), primary_key=True),
            Column('family_id', String(36), ForeignKey('families.id'), index=True),
            Column('from_member_id', String(36), ForeignKey('members.id'), index=True),
            Column('to_member_id', String(36), ForeignKey('members.id'), index=True),
            Column('amount', Float, default=0.0),
            Column('last_updated', DateTime(timezone=True), server_default=func.now())
        )
        
        # Crear las tablas en la base de datos
        metadata.create_all(engine)
        logger.info("Tablas de caché de balances creadas exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error al crear tablas de caché de balances: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_balance_cache_tables()
    if success:
        print("✅ Tablas de caché de balances creadas exitosamente.")
        print("Ahora debes:")
        print("1. Actualizar app/models/models.py con las clases MemberBalanceCache y DebtCache")
        print("2. Implementar los métodos de actualización en app/services/balance_service.py")
    else:
        print("❌ Error al crear las tablas de caché de balances.")
