"""
Script de prueba para verificar los cálculos de balances

Este script crea una familia con miembros, añade gastos y pagos,
y verifica que los balances se calculan correctamente.
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

def create_test_data():
    """Crea datos de prueba en la base de datos."""
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
        member1 = Member(
            id=generate_id(),
            name="Alex Mon",
            telegram_id="alex_test",
            family_id=family.id
        )
        
        member2 = Member(
            id=generate_id(),
            name="Denise",
            telegram_id="denise_test",
            family_id=family.id
        )
        
        db.add(member1)
        db.add(member2)
        db.commit()
        
        # Crear gastos
        # Gasto 1: Alex pagó $130 de gasolina, dividido entre ambos
        expense1 = Expense(
            id=generate_id(),
            description="Gasolina",
            amount=130.0,
            paid_by=member1.id,
            family_id=family.id
        )
        expense1.split_among = [member1, member2]
        
        # Gasto 2: Alex pagó $60 de aseo, dividido entre ambos
        expense2 = Expense(
            id=generate_id(),
            description="Aseo",
            amount=60.0,
            paid_by=member1.id,
            family_id=family.id
        )
        expense2.split_among = [member1, member2]
        
        # Gasto 3: Denise pagó $55 de comida, dividido entre ambos
        expense3 = Expense(
            id=generate_id(),
            description="Comida",
            amount=55.0,
            paid_by=member2.id,
            family_id=family.id
        )
        expense3.split_among = [member1, member2]
        
        # Gasto 4: Denise pagó $200 de internet, dividido entre ambos
        expense4 = Expense(
            id=generate_id(),
            description="Internet",
            amount=200.0,
            paid_by=member2.id,
            family_id=family.id
        )
        expense4.split_among = [member1, member2]
        
        db.add(expense1)
        db.add(expense2)
        db.add(expense3)
        db.add(expense4)
        db.commit()
        
        return family.id, member1.id, member2.id
    
    except Exception as e:
        db.rollback()
        raise e

def test_initial_balances(family_id):
    """Prueba los balances iniciales después de crear gastos."""
    db = next(get_db())
    try:
        # Calcular balances con modo debug activado
        print("Calculando balances iniciales...")
        try:
            balances = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        except Exception as e:
            print(f"Error al calcular balances: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"Balances calculados: {len(balances)}")
        
        # Verificar que la suma de todos los balances netos es cero
        total_net = sum(b.net_balance for b in balances)
        assert abs(total_net) < 0.01, f"La suma de los balances netos no es cero: {total_net}"
        
        # Imprimir los balances para verificación manual
        print("\n===== BALANCES INICIALES =====")
        for balance in balances:
            print(f"\n👤 {balance.name}")
            print(f"🔵 Balance neto: ${balance.net_balance:.2f}")
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
        
        return True
    
    except Exception as e:
        print(f"Error en test_initial_balances: {e}")
        import traceback
        traceback.print_exc()
        return False

def make_payment(family_id, from_member_id, to_member_id, amount):
    """Realiza un pago entre miembros."""
    db = next(get_db())
    try:
        # Crear el pago
        payment = Payment(
            id=generate_id(),
            from_member_id=from_member_id,
            to_member_id=to_member_id,
            amount=amount,
            family_id=family_id
        )
        
        db.add(payment)
        db.commit()
        
        print(f"\n✅ Pago creado: ${amount:.2f} de {from_member_id} a {to_member_id}")
        
        return True
    
    except Exception as e:
        db.rollback()
        print(f"Error al crear el pago: {e}")
        return False

def test_balances_after_payment(family_id):
    """Prueba los balances después de realizar un pago."""
    db = next(get_db())
    try:
        # Calcular balances con modo debug activado
        balances = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        
        # Verificar que la suma de todos los balances netos es cero
        total_net = sum(b.net_balance for b in balances)
        assert abs(total_net) < 0.01, f"La suma de los balances netos no es cero: {total_net}"
        
        # Imprimir los balances para verificación manual
        print("\n===== BALANCES DESPUÉS DEL PAGO =====")
        for balance in balances:
            print(f"\n👤 {balance.name}")
            print(f"🔵 Balance neto: ${balance.net_balance:.2f}")
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
        
        return True
    
    except Exception as e:
        print(f"Error en test_balances_after_payment: {e}")
        return False

def test_duplicate_payments(family_id, from_member_id, to_member_id):
    """Prueba la detección y corrección de pagos duplicados."""
    db = next(get_db())
    try:
        # Crear un pago duplicado para probar
        payment = Payment(
            id=generate_id(),
            from_member_id=from_member_id,
            to_member_id=to_member_id,
            amount=100.0,  # Mismo monto que el pago anterior
            family_id=family_id
        )
        db.add(payment)
        db.commit()
        
        # Obtener diagnóstico de pagos
        all_payments, duplicate_analysis = BalanceService.debug_payment_handling(db, family_id)
        
        # Imprimir información de diagnóstico
        print("\n===== DIAGNÓSTICO DE PAGOS =====")
        print(f"Total de pagos encontrados: {len(all_payments)}")
        
        if duplicate_analysis:
            print("\nPosibles pagos duplicados:")
            for dup in duplicate_analysis:
                print(f"• {dup['count']} pagos de ${dup['amount']} de {dup['from_member']} a {dup['to_member']}")
                print(f"  IDs: {', '.join(dup['payment_ids'])}")
                print(f"  Recomendación: {dup['recommendation']}")
        else:
            print("\nNo se encontraron pagos duplicados.")
        
        # Verificar consistencia de balances
        consistency = BalanceService.verify_balance_consistency(db, family_id)
        print(f"\nConsistencia de balances: {'✅ OK' if consistency else '❌ ERROR'}")
        
        return True
    
    except Exception as e:
        print(f"Error en test_duplicate_payments: {e}")
        return False

def fix_duplicate_payments(family_id):
    """Prueba la corrección automática de pagos duplicados."""
    db = next(get_db())
    try:
        # Obtener diagnóstico antes de la corrección
        print("\n===== ANTES DE CORREGIR PAGOS DUPLICADOS =====")
        all_payments_before, duplicate_analysis_before = BalanceService.debug_payment_handling(db, family_id)
        print(f"Total de pagos encontrados: {len(all_payments_before)}")
        
        # Verificar que hay duplicados para corregir
        if not duplicate_analysis_before:
            print("No se encontraron pagos duplicados para corregir.")
            return True
            
        print(f"Pagos duplicados encontrados: {len(duplicate_analysis_before)}")
        
        # Implementar corrección manual de duplicados (similar al endpoint fix-duplicates)
        payments_deleted = []
        
        # Agrupar pagos por la "firma" (origen, destino, monto)
        payments_by_signature = {}
        for payment in all_payments_before:
            signature = f"{payment['from_member']}->{payment['to_member']}-{payment['amount']}"
            
            if signature not in payments_by_signature:
                payments_by_signature[signature] = []
            
            payments_by_signature[signature].append({
                "id": payment["id"],
                "created_at": payment["created_at"]
            })
        
        # Para cada grupo de pagos duplicados, mantener solo el más reciente
        for signature, payments in payments_by_signature.items():
            if len(payments) <= 1:
                continue  # No es un duplicado
            
            # Ordenar por fecha de creación (del más reciente al más antiguo)
            sorted_payments = sorted(payments, key=lambda p: p["created_at"], reverse=True)
            
            # Mantener el más reciente, eliminar el resto
            for payment in sorted_payments[1:]:
                # Obtener el pago de la base de datos
                db_payment = db.query(Payment).filter(Payment.id == payment["id"]).first()
                if db_payment:
                    # Guardar información antes de eliminar
                    payment_info = {
                        "id": db_payment.id,
                        "from_member_id": db_payment.from_member_id,
                        "to_member_id": db_payment.to_member_id,
                        "amount": db_payment.amount
                    }
                    
                    # Eliminar el pago
                    db.delete(db_payment)
                    payments_deleted.append(payment_info)
        
        # Confirmar los cambios
        db.commit()
        
        print(f"Se eliminaron {len(payments_deleted)} pagos duplicados")
        
        # Obtener diagnóstico después de la corrección
        print("\n===== DESPUÉS DE CORREGIR PAGOS DUPLICADOS =====")
        all_payments_after, duplicate_analysis_after = BalanceService.debug_payment_handling(db, family_id)
        print(f"Total de pagos encontrados: {len(all_payments_after)}")
        
        if duplicate_analysis_after:
            print("ADVERTENCIA: Todavía hay pagos duplicados después de la corrección.")
            return False
        else:
            print("No hay pagos duplicados después de la corrección. ✅")
        
        # Calcular balances finales
        balances = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        
        # Imprimir los balances finales
        print("\n===== BALANCES FINALES (DESPUÉS DE CORRECCIÓN) =====")
        for balance in balances:
            print(f"\n👤 {balance.name}")
            print(f"🔵 Balance neto: ${balance.net_balance:.2f}")
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
        
        return True
    
    except Exception as e:
        print(f"Error en fix_duplicate_payments: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal que ejecuta todas las pruebas."""
    try:
        # Crear datos de prueba
        family_id, member1_id, member2_id = create_test_data()
        print(f"✅ Datos de prueba creados:")
        print(f"  - ID de familia: {family_id}")
        print(f"  - ID de miembro 1 (Alex): {member1_id}")
        print(f"  - ID de miembro 2 (Denise): {member2_id}")
        
        # Probar balances iniciales
        if test_initial_balances(family_id):
            print("✅ Prueba de balances iniciales completada")
        else:
            print("❌ Prueba de balances iniciales fallida")
            return
        
        # Realizar un pago
        if make_payment(family_id, member1_id, member2_id, 100.0):
            print("✅ Pago realizado correctamente")
        else:
            print("❌ Error al realizar el pago")
            return
        
        # Probar balances después del pago
        if test_balances_after_payment(family_id):
            print("✅ Prueba de balances después del pago completada")
        else:
            print("❌ Prueba de balances después del pago fallida")
            return
        
        # Probar diagnóstico de pagos duplicados
        if test_duplicate_payments(family_id, member1_id, member2_id):
            print("✅ Prueba de diagnóstico de pagos completada")
        else:
            print("❌ Prueba de diagnóstico de pagos fallida")
            return
            
        # Probar corrección de pagos duplicados
        if fix_duplicate_payments(family_id):
            print("✅ Prueba de corrección de pagos duplicados completada")
        else:
            print("❌ Prueba de corrección de pagos duplicados fallida")
            return
        
        print("\n✅ Todas las pruebas completadas con éxito")
    
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")

if __name__ == "__main__":
    main() 