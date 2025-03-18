"""
Script para probar el sistema de estados de pago

Este script crea un escenario de prueba para verificar que los pagos
pueden ser creados en estado PENDING y luego confirmados o rechazados.
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
from app.models.models import Family, Member, Expense, Payment, PaymentStatus
from app.models.schemas import PaymentCreate, PaymentUpdate
from app.services.payment_service import PaymentService
from app.services.balance_service import BalanceService
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

def test_payment_status_flow():
    """Prueba el flujo completo de estados de pago."""
    print("\n=== PRUEBA DEL FLUJO DE ESTADOS DE PAGO ===")
    
    # Crear escenario de prueba
    family_id, alex_id, denise_id = create_test_scenario()
    print(f"✅ Escenario de prueba creado:")
    print(f"  - Alex debe $50 a Denise")
    
    db = next(get_db())
    
    # Verificar balance inicial
    print("\n1. Verificando balance inicial:")
    balances = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
    alex_balance = next((b for b in balances if b.member_id == alex_id), None)
    print(f"  - Alex debe ${alex_balance.total_debt:.2f} en total")
    print(f"  - Número de pagos confirmados considerados: {len(db.query(Payment).filter_by(status=PaymentStatus.CONFIRM).all())}")
    
    # Caso 1: Crear un pago (debe estar en estado PENDING)
    payment_data = PaymentCreate(
        from_member=alex_id,
        to_member=denise_id,
        amount=30.0  # Pago parcial
    )
    
    try:
        payment = PaymentService.create_payment(db, payment_data, family_id)
        payment_id = payment.id
        print(f"\n2. Pago creado correctamente (ID: {payment_id})")
        print(f"  - Estado inicial: {payment.status.value}")
        
        if payment.status != PaymentStatus.PENDING:
            print(f"❌ ERROR: El estado inicial debería ser PENDING, pero es {payment.status.value}")
            return False
        else:
            print(f"✅ El estado inicial es PENDING como se esperaba")
        
        # Verificar que el pago no afecta el balance ya que está en PENDING
        balances_after_pending = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        alex_balance_after_pending = next((b for b in balances_after_pending if b.member_id == alex_id), None)
        
        if alex_balance.total_debt != alex_balance_after_pending.total_debt:
            print(f"❌ ERROR: El balance cambió aunque el pago está en PENDING")
            print(f"  - Deuda anterior: ${alex_balance.total_debt:.2f}")
            print(f"  - Deuda actual: ${alex_balance_after_pending.total_debt:.2f}")
            return False
        else:
            print(f"✅ El balance no cambió mientras el pago está en PENDING")
    
    except HTTPException as e:
        print(f"❌ ERROR: No se pudo crear el pago: {e.detail}")
        return False
    
    # Caso 2: Confirmar el pago (debe cambiar a CONFIRM y afectar el balance)
    try:
        payment = PaymentService.confirm_payment(db, payment_id)
        print(f"\n3. Pago confirmado correctamente")
        print(f"  - Nuevo estado: {payment.status.value}")
        
        if payment.status != PaymentStatus.CONFIRM:
            print(f"❌ ERROR: El estado debería ser CONFIRM, pero es {payment.status.value}")
            return False
        else:
            print(f"✅ El estado cambió a CONFIRM como se esperaba")
        
        # Verificar que el pago ahora sí afecta el balance
        balances_after_confirm = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        alex_balance_after_confirm = next((b for b in balances_after_confirm if b.member_id == alex_id), None)
        
        expected_debt = alex_balance.total_debt - payment.amount
        
        if abs(alex_balance_after_confirm.total_debt - expected_debt) > 0.01:
            print(f"❌ ERROR: El balance no se actualizó correctamente después de confirmar")
            print(f"  - Deuda esperada: ${expected_debt:.2f}")
            print(f"  - Deuda actual: ${alex_balance_after_confirm.total_debt:.2f}")
            return False
        else:
            print(f"✅ El balance se actualizó correctamente después de confirmar")
            print(f"  - Deuda original: ${alex_balance.total_debt:.2f}")
            print(f"  - Pago realizado: ${payment.amount:.2f}")
            print(f"  - Deuda actual: ${alex_balance_after_confirm.total_debt:.2f}")
    
    except HTTPException as e:
        print(f"❌ ERROR: No se pudo confirmar el pago: {e.detail}")
        return False
    
    # Caso 3: Crear un segundo pago y rechazarlo
    payment_data2 = PaymentCreate(
        from_member=alex_id,
        to_member=denise_id,
        amount=10.0
    )
    
    try:
        payment2 = PaymentService.create_payment(db, payment_data2, family_id)
        payment2_id = payment2.id
        print(f"\n4. Segundo pago creado correctamente (ID: {payment2_id})")
        print(f"  - Estado inicial: {payment2.status.value}")
        
        # Rechazar el pago
        payment2 = PaymentService.reject_payment(db, payment2_id)
        print(f"\n5. Pago rechazado correctamente")
        print(f"  - Nuevo estado: {payment2.status.value}")
        
        if payment2.status != PaymentStatus.INACTIVE:
            print(f"❌ ERROR: El estado debería ser INACTIVE, pero es {payment2.status.value}")
            return False
        else:
            print(f"✅ El estado cambió a INACTIVE como se esperaba")
        
        # Verificar que el pago rechazado no afecta el balance
        balances_after_reject = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        alex_balance_after_reject = next((b for b in balances_after_reject if b.member_id == alex_id), None)
        
        if abs(alex_balance_after_confirm.total_debt - alex_balance_after_reject.total_debt) > 0.01:
            print(f"❌ ERROR: El balance cambió después de rechazar el pago")
            print(f"  - Deuda antes del rechazo: ${alex_balance_after_confirm.total_debt:.2f}")
            print(f"  - Deuda después del rechazo: ${alex_balance_after_reject.total_debt:.2f}")
            return False
        else:
            print(f"✅ El balance no cambió después de rechazar el pago")
    
    except HTTPException as e:
        print(f"❌ ERROR: Problema con el segundo pago: {e.detail}")
        return False
    
    return True

def main():
    """Función principal."""
    try:
        if test_payment_status_flow():
            print("\n✅ TODAS LAS PRUEBAS PASADAS: El sistema de estados de pago funciona correctamente")
        else:
            print("\n❌ PRUEBAS FALLIDAS: Hay problemas con el sistema de estados de pago")
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 