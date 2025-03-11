"""
Script para probar la validación de pagos excesivos

Este script crea un escenario de prueba para verificar que el sistema
rechaza pagos que exceden la deuda total entre miembros.
"""

import sys
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Añadir el directorio raíz al path para importar los módulos de la aplicación
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.models.database import Base
from app.models.models import Family, Member, Expense, Payment
from app.models.schemas import PaymentCreate
from app.services.payment_service import PaymentService
from fastapi import HTTPException

# Usar SQLite en memoria para las pruebas
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

def generate_id():
    """Genera un ID único para las entidades."""
    return str(uuid.uuid4())

def get_db():
    """Obtener una sesión de base de datos para las pruebas."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_test_scenario():
    """
    Crea un escenario de prueba con dos miembros y una deuda específica.
    
    Escenario: 
    - Alex debe $50 a Denise
    """
    db = next(get_db())
    try:
        # Crear una familia
        family = Family(
            id=generate_id(),
            name="Familia de Prueba"
        )
        db.add(family)
        db.commit()
        
        # Crear miembros con IDs de Telegram únicos
        alex = Member(
            id=generate_id(),
            name="Alex",
            telegram_id=f"alex_test_{generate_id()}",
            family_id=family.id
        )
        
        denise = Member(
            id=generate_id(),
            name="Denise",
            telegram_id=f"denise_test_{generate_id()}",
            family_id=family.id
        )
        
        db.add(alex)
        db.add(denise)
        db.commit()
        
        # Crear un gasto para generar la deuda
        # Denise pagó $100, de los cuales $50 corresponden a Alex
        expense = Expense(
            id=generate_id(),
            description="Gasto compartido",
            amount=100.0,
            paid_by=denise.id,
            family_id=family.id
        )
        expense.split_among = [alex, denise]
        
        db.add(expense)
        db.commit()
        
        return family.id, alex.id, denise.id
    
    except Exception as e:
        db.rollback()
        raise e

def test_payment_validation():
    """Prueba la validación de pagos excesivos."""
    print("\n=== PRUEBA DE VALIDACIÓN DE PAGOS EXCESIVOS ===")
    
    # Crear escenario de prueba
    family_id, alex_id, denise_id = create_test_scenario()
    print(f"✅ Escenario de prueba creado:")
    print(f"  - Alex debe $50 a Denise")
    
    db = next(get_db())
    
    # Caso 1: Pago exactamente igual a la deuda (debe funcionar)
    payment_data_exact = PaymentCreate(
        from_member=alex_id,
        to_member=denise_id,
        amount=50.0
    )
    
    try:
        payment = PaymentService.create_payment(db, payment_data_exact, family_id)
        print("✅ Pago exacto aceptado correctamente")
        
        # Eliminar el pago para la siguiente prueba
        db.delete(payment)
        db.commit()
    except HTTPException as e:
        print(f"❌ ERROR: El pago exacto debería ser aceptado: {e.detail}")
        return False
    
    # Caso 2: Pago que excede la deuda (debe ser rechazado)
    payment_data_excessive = PaymentCreate(
        from_member=alex_id,
        to_member=denise_id,
        amount=75.0  # Excede la deuda de $50
    )
    
    try:
        PaymentService.create_payment(db, payment_data_excessive, family_id)
        print("❌ ERROR: Se aceptó un pago que excede la deuda")
        return False
    except HTTPException as e:
        print(f"✅ Pago excesivo rechazado correctamente: {e.detail}")
    
    # Caso 3: Pago en dirección incorrecta (Denise a Alex cuando Alex debe a Denise)
    payment_data_wrong_direction = PaymentCreate(
        from_member=denise_id,
        to_member=alex_id,
        amount=25.0
    )
    
    try:
        PaymentService.create_payment(db, payment_data_wrong_direction, family_id)
        print("❌ ERROR: Se aceptó un pago en dirección incorrecta")
        return False
    except HTTPException as e:
        print(f"✅ Pago en dirección incorrecta rechazado correctamente: {e.detail}")
    
    # Caso 4: Pago parcial (debe funcionar)
    payment_data_partial = PaymentCreate(
        from_member=alex_id,
        to_member=denise_id,
        amount=25.0  # Pago parcial de la deuda
    )
    
    try:
        PaymentService.create_payment(db, payment_data_partial, family_id)
        print("✅ Pago parcial aceptado correctamente")
    except HTTPException as e:
        print(f"❌ ERROR: El pago parcial debería ser aceptado: {e.detail}")
        return False
    
    return True

def main():
    """Función principal."""
    try:
        if test_payment_validation():
            print("\n✅ TODAS LAS PRUEBAS PASADAS: La validación de pagos funciona correctamente")
        else:
            print("\n❌ PRUEBAS FALLIDAS: Hay problemas con la validación de pagos")
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 