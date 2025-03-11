"""
Pruebas aisladas para el BalanceService.

Este módulo contiene pruebas unitarias para el servicio de balance de la aplicación
real, utilizando mocks para aislar la lógica de negocio de la base de datos.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Importar el servicio real
from app.services.balance_service import BalanceService
from app.models.models import Family, Member, Expense, Payment

class TestIsolatedBalanceService(unittest.TestCase):
    """
    Pruebas unitarias aisladas para el servicio de balance.
    """
    
    def setUp(self):
        """
        Configuración común para las pruebas.
        """
        # Crear mock de la sesión de base de datos
        self.mock_db = MagicMock()
        
        # Crear miembros mock
        self.member1 = MagicMock(spec=Member)
        self.member1.id = "member-1"
        self.member1.name = "Juan Pérez"
        self.member1.family_id = "family-1"
        
        self.member2 = MagicMock(spec=Member)
        self.member2.id = "member-2"
        self.member2.name = "María López"
        self.member2.family_id = "family-1"
    
    def test_simple_balance_calculation(self):
        """
        Prueba el cálculo simple de balance con un gasto dividido entre dos miembros.
        """
        # Configurar los miembros
        members = [self.member1, self.member2]
        
        # Crear un gasto mock
        expense = MagicMock(spec=Expense)
        expense.id = "expense-1"
        expense.description = "Comida"
        expense.amount = 100.0
        expense.paid_by = "member-1"
        expense.family_id = "family-1"
        expense.split_among = members
        
        # Configurar los mocks para responder a las consultas
        self.mock_db.query.return_value.filter.return_value.all.side_effect = [
            members,     # Para obtener los miembros de la familia
            [expense],   # Para obtener los gastos
            [],          # Para obtener los pagos (payments_from)
            []           # Para obtener los pagos (payments_to)
        ]
        
        # Ejecutar el método a probar
        results = BalanceService.calculate_family_balances(self.mock_db, "family-1")
        
        # Verificar que se llama a la base de datos correctamente
        self.mock_db.query.assert_called()
        
        # Verificar que hay resultados para ambos miembros
        self.assertEqual(len(results), 2)
        
        # Encontrar los balances de cada miembro
        juan_balance = next((b for b in results if b.member_id == "member-1"), None)
        maria_balance = next((b for b in results if b.member_id == "member-2"), None)
        
        # Verificar que se encontraron los balances
        self.assertIsNotNone(juan_balance)
        self.assertIsNotNone(maria_balance)
        
        # Verificar el balance de Juan (pagó 100, su parte es 50, debe recibir 50)
        self.assertEqual(juan_balance.total_debt, 0.0)
        self.assertEqual(juan_balance.total_owed, 50.0)
        self.assertEqual(juan_balance.net_balance, 50.0)
        self.assertEqual(len(juan_balance.credits), 1)
        self.assertEqual(juan_balance.credits[0].from_, "María López")
        self.assertEqual(juan_balance.credits[0].amount, 50.0)
        
        # Verificar el balance de María (debe 50 a Juan)
        self.assertEqual(maria_balance.total_debt, 50.0)
        self.assertEqual(maria_balance.total_owed, 0.0)
        self.assertEqual(maria_balance.net_balance, -50.0)
        self.assertEqual(len(maria_balance.debts), 1)
        self.assertEqual(maria_balance.debts[0].to, "Juan Pérez")
        self.assertEqual(maria_balance.debts[0].amount, 50.0)
        
        # La suma de los balances netos debe ser cero
        sum_balance = juan_balance.net_balance + maria_balance.net_balance
        self.assertEqual(sum_balance, 0.0)
    
    def test_complex_balance_with_three_members(self):
        """
        Prueba compleja con tres miembros, múltiples gastos y pagos.
        """
        # Crear el tercer miembro
        member3 = MagicMock(spec=Member)
        member3.id = "member-3"
        member3.name = "Carlos Rodríguez"
        member3.family_id = "family-1"
        
        members = [self.member1, self.member2, member3]
        
        # Crear gastos mock
        # 1. Comida: Juan paga $120, dividido entre los 3
        expense1 = MagicMock(spec=Expense)
        expense1.id = "expense-1"
        expense1.description = "Comida"
        expense1.amount = 120.0
        expense1.paid_by = "member-1"
        expense1.family_id = "family-1"
        expense1.split_among = members
        
        # 2. Cine: María paga $60, dividido entre María y Carlos
        expense2 = MagicMock(spec=Expense)
        expense2.id = "expense-2"
        expense2.description = "Cine"
        expense2.amount = 60.0
        expense2.paid_by = "member-2"
        expense2.family_id = "family-1"
        expense2.split_among = [self.member2, member3]
        
        # 3. Supermercado: Carlos paga $90, dividido entre los 3
        expense3 = MagicMock(spec=Expense)
        expense3.id = "expense-3"
        expense3.description = "Supermercado"
        expense3.amount = 90.0
        expense3.paid_by = "member-3"
        expense3.family_id = "family-1"
        expense3.split_among = members
        
        expenses = [expense1, expense2, expense3]
        
        # Crear pagos mock
        # 1. Carlos paga $20 a Juan
        payment1 = MagicMock(spec=Payment)
        payment1.id = "payment-1"
        payment1.from_member_id = "member-3"
        payment1.to_member_id = "member-1"
        payment1.amount = 20.0
        payment1.family_id = "family-1"
        
        # 2. María paga $15 a Carlos
        payment2 = MagicMock(spec=Payment)
        payment2.id = "payment-2"
        payment2.from_member_id = "member-2"
        payment2.to_member_id = "member-3"
        payment2.amount = 15.0
        payment2.family_id = "family-1"
        
        payments = [payment1, payment2]
        
        # Configurar los mocks para responder a las consultas
        self.mock_db.query.return_value.filter.return_value.all.side_effect = [
            members,             # Para obtener los miembros de la familia
            expenses,            # Para obtener los gastos
            payments,            # Para obtener los pagos (payments_from)
            []                   # Para obtener los pagos (payments_to)
        ]
        
        # Ejecutar el método a probar
        results = BalanceService.calculate_family_balances(self.mock_db, "family-1")
        
        # Verificar que hay resultados para los tres miembros
        self.assertEqual(len(results), 3)
        
        # Encontrar los balances de cada miembro
        juan_balance = next((b for b in results if b.member_id == "member-1"), None)
        maria_balance = next((b for b in results if b.member_id == "member-2"), None)
        carlos_balance = next((b for b in results if b.member_id == "member-3"), None)
        
        # Imprimir resultados detallados para diagnóstico
        print("\nResultados calculados por el servicio real:")
        for balance in results:
            print(f"\n{balance.name}:")
            print(f"  ID: {balance.member_id}")
            print(f"  Total deuda: ${balance.total_debt:.2f}")
            print(f"  Total a recibir: ${balance.total_owed:.2f}")
            print(f"  Balance neto: ${balance.net_balance:.2f}")
            
            if balance.debts:
                print("  Debe a:")
                for debt in balance.debts:
                    print(f"    {debt.to}: ${debt.amount:.2f}")
            
            if balance.credits:
                print("  Le deben:")
                for credit in balance.credits:
                    print(f"    {credit.from_}: ${credit.amount:.2f}")

if __name__ == "__main__":
    unittest.main() 