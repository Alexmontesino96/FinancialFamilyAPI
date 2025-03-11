"""
Script para probar la visualización de deudas y créditos

Este script crea un escenario de prueba con dos miembros que se deben dinero mutuamente
y verifica que los balances se visualicen correctamente con deudas netas.
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
from app.services.balance_service import BalanceService

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

def create_test_scenario_1():
    """
    Crea un escenario de prueba con dos miembros y gastos que generan deudas mutuas.
    
    Escenario: 
    - Alex pagó $75 (dividido entre ambos)
    - Denise pagó $50 (dividido entre ambos)
    
    Resultado esperado:
    - Alex debe $37.50 a Denise
    - Denise debe $25.00 a Alex
    - Deuda neta: Alex debe $12.50 a Denise
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
        
        # Crear miembros
        alex = Member(
            id=generate_id(),
            name="Alex",
            telegram_id="alex_test",
            family_id=family.id
        )
        
        denise = Member(
            id=generate_id(),
            name="Denise",
            telegram_id="denise_test",
            family_id=family.id
        )
        
        db.add(alex)
        db.add(denise)
        db.commit()
        
        # Crear gastos
        # Gasto 1: Alex pagó $75, dividido entre ambos
        expense1 = Expense(
            id=generate_id(),
            description="Gasto de Alex",
            amount=75.0,
            paid_by=alex.id,
            family_id=family.id
        )
        expense1.split_among = [alex, denise]
        
        # Gasto 2: Denise pagó $50, dividido entre ambos
        expense2 = Expense(
            id=generate_id(),
            description="Gasto de Denise",
            amount=50.0,
            paid_by=denise.id,
            family_id=family.id
        )
        expense2.split_among = [alex, denise]
        
        db.add(expense1)
        db.add(expense2)
        db.commit()
        
        return family.id, alex.id, denise.id
    
    except Exception as e:
        db.rollback()
        raise e

def create_test_scenario_2():
    """
    Crea un escenario de prueba exactamente como el descrito en el problema del usuario.
    
    Escenario: 
    - Alex debe a Denise: $75.00
    - Denise debe a Alex: $50.00
    
    Resultado esperado:
    - Deuda neta: Alex debe $25.00 a Denise
    """
    db = next(get_db())
    try:
        # Crear una familia
        family = Family(
            id=generate_id(),
            name="Familia de Prueba 2"
        )
        db.add(family)
        db.commit()
        
        # Crear miembros con IDs de Telegram únicos
        alex = Member(
            id=generate_id(),
            name="Alex",
            telegram_id=f"alex_test_{generate_id()}",  # ID único
            family_id=family.id
        )
        
        denise = Member(
            id=generate_id(),
            name="Denise",
            telegram_id=f"denise_test_{generate_id()}",  # ID único
            family_id=family.id
        )
        
        db.add(alex)
        db.add(denise)
        db.commit()
        
        # Crear gastos específicos para replicar el problema
        # Gasto 1: Denise pagó $150, de los cuales $75 corresponden a Alex
        expense1 = Expense(
            id=generate_id(),
            description="Gasto grande de Denise",
            amount=150.0,
            paid_by=denise.id,
            family_id=family.id
        )
        expense1.split_among = [alex, denise]
        
        # Gasto 2: Alex pagó $100, de los cuales $50 corresponden a Denise
        expense2 = Expense(
            id=generate_id(),
            description="Gasto grande de Alex",
            amount=100.0,
            paid_by=alex.id,
            family_id=family.id
        )
        expense2.split_among = [alex, denise]
        
        db.add(expense1)
        db.add(expense2)
        db.commit()
        
        return family.id, alex.id, denise.id
    
    except Exception as e:
        db.rollback()
        raise e

def test_balance_display(family_id):
    """Prueba la visualización de balances."""
    db = next(get_db())
    try:
        # Calcular balances con modo debug activado
        print("Calculando balances...")
        balances = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        
        # Verificar que la suma de todos los balances netos es cero
        total_net = sum(b.net_balance for b in balances)
        assert abs(total_net) < 0.01, f"La suma de los balances netos no es cero: {total_net}"
        
        # Imprimir los balances para verificación manual
        print("\n===== BALANCES CALCULADOS =====")
        for balance in balances:
            print(f"\n👤 {balance.name}")
            print(f"{'🔴' if balance.net_balance < 0 else '🟢'} Balance neto: ${balance.net_balance:.2f}")
            print(f"💰 Total a favor: ${balance.total_owed:.2f}")
            print(f"💸 Total a deber: ${balance.total_debt:.2f}")
            
            print("\nDeudas:")
            if balance.debts:
                for debt in balance.debts:
                    print(f"• Debe a {debt.to}: ${debt.amount:.2f}")
            else:
                print("• No debe a nadie")
            
            print("\nCréditos:")
            if balance.credits:
                for credit in balance.credits:
                    print(f"• Le debe {credit.from_}: ${credit.amount:.2f}")
            else:
                print("• Nadie le debe")
        
        # Verificar que no hay deudas mutuas (si A debe a B, B no debería deber a A)
        debtors = {}
        for balance in balances:
            for debt in balance.debts:
                debtors.setdefault(balance.name, set()).add(debt.to)
        
        for debtor, creditors in debtors.items():
            for creditor in creditors:
                # Verificar que el acreedor no debe al deudor
                creditor_balance = next((b for b in balances if b.name == creditor), None)
                if creditor_balance:
                    creditor_debtors = {debt.to for debt in creditor_balance.debts}
                    assert debtor not in creditor_debtors, f"Deuda mutua detectada: {debtor} debe a {creditor} y {creditor} debe a {debtor}"
        
        print("\n✅ La visualización de balances es correcta. No hay deudas mutuas.")
        
        return balances
    
    except Exception as e:
        print(f"❌ Error en test_balance_display: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Función principal que ejecuta las pruebas."""
    try:
        print("=== ESCENARIO 1: Gastos divididos ===")
        # Crear datos de prueba para el escenario 1
        family_id, alex_id, denise_id = create_test_scenario_1()
        print(f"✅ Datos de prueba creados para el escenario 1:")
        print(f"  - ID de familia: {family_id}")
        print(f"  - ID de Alex: {alex_id}")
        print(f"  - ID de Denise: {denise_id}")
        
        # Probar visualización de balances
        balances1 = test_balance_display(family_id)
        if balances1:
            print("✅ Escenario 1 completado con éxito")
        else:
            print("❌ Escenario 1 fallido")
        
        print("\n=== ESCENARIO 2: Replicación del problema reportado ===")
        # Crear datos de prueba para el escenario 2
        family_id2, alex_id2, denise_id2 = create_test_scenario_2()
        print(f"✅ Datos de prueba creados para el escenario 2:")
        print(f"  - ID de familia: {family_id2}")
        print(f"  - ID de Alex: {alex_id2}")
        print(f"  - ID de Denise: {denise_id2}")
        
        # Probar visualización de balances
        balances2 = test_balance_display(family_id2)
        if balances2:
            print("✅ Escenario 2 completado con éxito")
        else:
            print("❌ Escenario 2 fallido")
        
        print("\n✅ Todas las pruebas completadas")
    
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 