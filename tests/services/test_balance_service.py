import pytest
from unittest.mock import MagicMock
from app.services.balance_service import BalanceService
from .test_base import TestBase

class TestBalanceService(TestBase):
    """
    Pruebas unitarias para el servicio de balance.
    """
    
    def test_calculate_family_balances_simple(self, mock_db):
        """
        Prueba el cálculo de saldos para un caso simple:
        - 2 miembros
        - 1 gasto dividido equitativamente
        - Sin pagos
        """
        # Crear miembros mock
        member1 = self.create_mock_member(
            id="member-uuid-1",
            name="Juan Pérez",
            family_id="family-uuid-1"
        )
        
        member2 = self.create_mock_member(
            id="member-uuid-2",
            name="María López",
            family_id="family-uuid-1"
        )
        
        # Crear un gasto mock
        expense = self.create_mock_expense(
            id="expense-uuid-1",
            description="Comida",
            amount=100.0,
            paid_by="member-uuid-1",
            family_id="family-uuid-1",
            split_among=[member1, member2]
        )
        
        # Configurar los mocks para las consultas
        mock_members_query = self.setup_mock_query(mock_db, result_list=[member1, member2])
        
        # Configurar una segunda llamada a query para los gastos
        mock_db.query.side_effect = [
            mock_members_query,  # Para members
            mock_members_query,  # Para expense.paid_by.in_
        ]
        
        # Configurar el resultado de expenses
        mock_members_query.filter.return_value.all.side_effect = [
            [member1, member2],  # Para members
            [expense]            # Para expenses
        ]
        
        # Crear un diccionario para buscar miembros por ID
        members_by_id = {str(m.id): m for m in [member1, member2]}
        
        # Ejecutar el método a probar
        result = BalanceService.calculate_family_balances(mock_db, "family-uuid-1")
        
        # Verificar los resultados
        assert len(result) == 2
        
        # Verificar balances de Juan (pagó 100, debe recibir 50 de María)
        juan_balance = next(b for b in result if b.name == "Juan Pérez")
        assert juan_balance.total_debt == 0.0
        assert juan_balance.total_owed == 50.0
        assert juan_balance.net_balance == 50.0
        assert len(juan_balance.credits) == 1
        assert juan_balance.credits[0].from_ == "María López"
        assert juan_balance.credits[0].amount == 50.0
        
        # Verificar balances de María (debe 50 a Juan)
        maria_balance = next(b for b in result if b.name == "María López")
        assert maria_balance.total_debt == 50.0
        assert maria_balance.total_owed == 0.0
        assert maria_balance.net_balance == -50.0
        assert len(maria_balance.debts) == 1
        assert maria_balance.debts[0].to == "Juan Pérez"
        assert maria_balance.debts[0].amount == 50.0
    
    def test_calculate_family_balances_with_payment(self, mock_db):
        """
        Prueba el cálculo de saldos con un pago:
        - 2 miembros
        - 1 gasto dividido equitativamente
        - 1 pago que salda parte de la deuda
        """
        # Crear miembros mock
        member1 = self.create_mock_member(
            id="member-uuid-1", 
            name="Juan Pérez",
            family_id="family-uuid-1"
        )
        
        member2 = self.create_mock_member(
            id="member-uuid-2",
            name="María López",
            family_id="family-uuid-1"
        )
        
        # Crear un gasto mock
        expense = self.create_mock_expense(
            id="expense-uuid-1",
            description="Comida",
            amount=100.0,
            paid_by="member-uuid-1",
            family_id="family-uuid-1",
            split_among=[member1, member2]
        )
        
        # Crear un pago mock (María paga 30 a Juan)
        payment = self.create_mock_payment(
            id="payment-uuid-1",
            from_member_id="member-uuid-2",
            to_member_id="member-uuid-1",
            amount=30.0,
            family_id="family-uuid-1"
        )
        
        # Configurar los mocks para las consultas
        mock_members_query = self.setup_mock_query(mock_db, result_list=[member1, member2])
        
        # Configurar múltiples llamadas a query
        mock_db.query.side_effect = [
            mock_members_query,  # Para members
            mock_members_query,  # Para expense.paid_by.in_
            mock_members_query,  # Para payments_from
            mock_members_query   # Para payments_to
        ]
        
        # Configurar los resultados
        mock_members_query.filter.return_value.all.side_effect = [
            [member1, member2],  # Para members
            [expense],           # Para expenses
            [payment],           # Para payments_from
            []                   # Para payments_to
        ]
        
        # Ejecutar el método a probar
        result = BalanceService.calculate_family_balances(mock_db, "family-uuid-1")
        
        # Verificar los resultados
        assert len(result) == 2
        
        # Verificar balances de Juan (pagó 100, recibió 30, le deben 20)
        juan_balance = next(b for b in result if b.name == "Juan Pérez")
        assert juan_balance.total_debt == 0.0
        assert juan_balance.total_owed == 20.0
        assert juan_balance.net_balance == 20.0
        assert len(juan_balance.credits) == 1
        assert juan_balance.credits[0].from_ == "María López"
        assert juan_balance.credits[0].amount == 20.0
        
        # Verificar balances de María (debía 50, pagó 30, debe 20)
        maria_balance = next(b for b in result if b.name == "María López")
        assert maria_balance.total_debt == 20.0
        assert maria_balance.total_owed == 0.0
        assert maria_balance.net_balance == -20.0
        assert len(maria_balance.debts) == 1
        assert maria_balance.debts[0].to == "Juan Pérez"
        assert maria_balance.debts[0].amount == 20.0
    
    def test_calculate_family_balances_multiple_expenses(self, mock_db):
        """
        Prueba el cálculo de saldos con múltiples gastos:
        - 2 miembros
        - Múltiples gastos pagados por diferentes miembros
        """
        # Crear miembros mock
        member1 = self.create_mock_member(
            id="member-uuid-1",
            name="Juan Pérez",
            family_id="family-uuid-1"
        )
        
        member2 = self.create_mock_member(
            id="member-uuid-2",
            name="María López",
            family_id="family-uuid-1"
        )
        
        # Crear gastos mock
        expense1 = self.create_mock_expense(
            id="expense-uuid-1",
            description="Comida",
            amount=100.0,
            paid_by="member-uuid-1",
            family_id="family-uuid-1",
            split_among=[member1, member2]
        )
        
        expense2 = self.create_mock_expense(
            id="expense-uuid-2",
            description="Cine",
            amount=40.0,
            paid_by="member-uuid-2",
            family_id="family-uuid-1",
            split_among=[member1, member2]
        )
        
        # Configurar los mocks para las consultas
        mock_members_query = self.setup_mock_query(mock_db, result_list=[member1, member2])
        
        # Configurar múltiples llamadas a query
        mock_db.query.side_effect = [
            mock_members_query,  # Para members
            mock_members_query,  # Para expense.paid_by.in_
            mock_members_query,  # Para payments_from
            mock_members_query   # Para payments_to
        ]
        
        # Configurar los resultados
        mock_members_query.filter.return_value.all.side_effect = [
            [member1, member2],        # Para members
            [expense1, expense2],      # Para expenses
            [],                        # Para payments_from
            []                         # Para payments_to
        ]
        
        # Ejecutar el método a probar
        result = BalanceService.calculate_family_balances(mock_db, "family-uuid-1")
        
        # Verificar los resultados
        assert len(result) == 2
        
        # Verificar balances de Juan (pagó 100, su parte del cine es 20, neto: debe recibir 30)
        juan_balance = next(b for b in result if b.name == "Juan Pérez")
        assert juan_balance.total_debt == 20.0
        assert juan_balance.total_owed == 50.0
        assert juan_balance.net_balance == 30.0
        assert len(juan_balance.credits) == 1
        assert juan_balance.credits[0].from_ == "María López"
        assert juan_balance.credits[0].amount == 50.0
        
        # Verificar balances de María (pagó 40, su parte de la comida es 50, neto: debe 10)
        maria_balance = next(b for b in result if b.name == "María López")
        assert maria_balance.total_debt == 50.0
        assert maria_balance.total_owed == 20.0
        assert maria_balance.net_balance == -30.0
        assert len(maria_balance.debts) == 1
        assert maria_balance.debts[0].to == "Juan Pérez"
        assert maria_balance.debts[0].amount == 50.0
    
    def test_get_member_balance(self, mock_db):
        """
        Prueba la obtención del balance de un miembro específico.
        """
        # Crear miembros mock
        member1 = self.create_mock_member(
            id="member-uuid-1",
            name="Juan Pérez",
            family_id="family-uuid-1"
        )
        
        member2 = self.create_mock_member(
            id="member-uuid-2",
            name="María López",
            family_id="family-uuid-1"
        )
        
        # Crear un gasto mock
        expense = self.create_mock_expense(
            id="expense-uuid-1",
            description="Comida",
            amount=100.0,
            paid_by="member-uuid-1",
            family_id="family-uuid-1",
            split_among=[member1, member2]
        )
        
        # Configurar los mocks para las consultas
        mock_members_query = self.setup_mock_query(mock_db, result_list=[member1, member2])
        
        # Configurar múltiples llamadas a query
        mock_db.query.side_effect = [
            mock_members_query,  # Para members
            mock_members_query,  # Para expense.paid_by.in_
            mock_members_query,  # Para payments_from
            mock_members_query   # Para payments_to
        ]
        
        # Configurar los resultados
        mock_members_query.filter.return_value.all.side_effect = [
            [member1, member2],  # Para members
            [expense],           # Para expenses
            [],                  # Para payments_from
            []                   # Para payments_to
        ]
        
        # Ejecutar el método a probar
        result = BalanceService.get_member_balance(mock_db, "family-uuid-1", "member-uuid-2")
        
        # Verificar que el resultado es el correcto
        assert result is not None
        assert result.member_id == "member-uuid-2"
        assert result.name == "María López"
        assert result.total_debt == 50.0
        assert result.total_owed == 0.0
        assert result.net_balance == -50.0
        assert len(result.debts) == 1
        assert result.debts[0].to == "Juan Pérez"
        assert result.debts[0].amount == 50.0
    
    def test_complex_balance_with_three_members(self, mock_db):
        """
        Prueba compleja del cálculo de saldos con 3 miembros, múltiples gastos y pagos.
        
        Escenario:
        - 3 miembros: Juan, María y Carlos
        - Gastos: 
            * Comida (pagado por Juan): $120 (dividido entre los 3)
            * Cine (pagado por María): $60 (dividido entre María y Carlos)
            * Supermercado (pagado por Carlos): $90 (dividido entre los 3)
        - Pagos:
            * Carlos paga a Juan: $20
            * María paga a Carlos: $15
        """
        # Crear miembros mock
        member1 = self.create_mock_member(
            id="member-uuid-1",
            name="Juan Pérez",
            family_id="family-uuid-1"
        )
        
        member2 = self.create_mock_member(
            id="member-uuid-2",
            name="María López",
            family_id="family-uuid-1"
        )
        
        member3 = self.create_mock_member(
            id="member-uuid-3",
            name="Carlos Rodríguez",
            family_id="family-uuid-1"
        )
        
        # Crear gastos mock
        # 1. Comida: Juan paga $120, dividido entre los 3
        expense1 = self.create_mock_expense(
            id="expense-uuid-1",
            description="Comida",
            amount=120.0,
            paid_by="member-uuid-1",
            family_id="family-uuid-1",
            split_among=[member1, member2, member3]
        )
        
        # 2. Cine: María paga $60, dividido entre María y Carlos
        expense2 = self.create_mock_expense(
            id="expense-uuid-2",
            description="Cine",
            amount=60.0,
            paid_by="member-uuid-2",
            family_id="family-uuid-1",
            split_among=[member2, member3]
        )
        
        # 3. Supermercado: Carlos paga $90, dividido entre los 3
        expense3 = self.create_mock_expense(
            id="expense-uuid-3",
            description="Supermercado",
            amount=90.0,
            paid_by="member-uuid-3",
            family_id="family-uuid-1",
            split_among=[member1, member2, member3]
        )
        
        # Crear pagos mock
        # 1. Carlos paga $20 a Juan
        payment1 = self.create_mock_payment(
            id="payment-uuid-1",
            from_member_id="member-uuid-3",
            to_member_id="member-uuid-1",
            amount=20.0,
            family_id="family-uuid-1"
        )
        
        # 2. María paga $15 a Carlos
        payment2 = self.create_mock_payment(
            id="payment-uuid-2",
            from_member_id="member-uuid-2",
            to_member_id="member-uuid-3",
            amount=15.0,
            family_id="family-uuid-1"
        )
        
        # Configurar los mocks para las consultas
        mock_members_query = self.setup_mock_query(mock_db, result_list=[member1, member2, member3])
        
        # Configurar múltiples llamadas a query
        mock_db.query.side_effect = [
            mock_members_query,  # Para members
            mock_members_query,  # Para expense.paid_by.in_
            mock_members_query,  # Para payments_from
            mock_members_query   # Para payments_to
        ]
        
        # Configurar los resultados
        mock_members_query.filter.return_value.all.side_effect = [
            [member1, member2, member3],              # Para members
            [expense1, expense2, expense3],           # Para expenses
            [payment1, payment2],                     # Para payments_from
            []                                        # Para payments_to
        ]
        
        # Ejecutar el método a probar
        result = BalanceService.calculate_family_balances(mock_db, "family-uuid-1")
        
        # Verificar los resultados
        assert len(result) == 3
        
        # ------ Verificar balance de Juan ------
        # Juan pagó $120 por comida (su parte: $40)
        # Juan debe $30 por su parte del supermercado
        # Juan recibió $20 de Carlos como pago
        # Total deuda: $30
        # Total recibido: $80 (de otros por comida) + $20 (pago de Carlos) = $100
        # Neto: +$70
        juan_balance = next(b for b in result if b.name == "Juan Pérez")
        assert round(juan_balance.total_debt, 2) == 30.0
        assert round(juan_balance.total_owed, 2) == 100.0
        assert round(juan_balance.net_balance, 2) == 70.0
        
        # ------ Verificar balance de María ------
        # María pagó $60 por cine (su parte: $30)
        # María debe $40 por su parte de comida
        # María debe $30 por su parte del supermercado
        # María pagó $15 a Carlos
        # Total deuda: $40 + $30 = $70
        # Total recibido: $30 (de Carlos por cine)
        # Neto: -$40
        maria_balance = next(b for b in result if b.name == "María López")
        assert round(maria_balance.total_debt, 2) == 70.0
        assert round(maria_balance.total_owed, 2) == 30.0
        assert round(maria_balance.net_balance, 2) == -40.0
        
        # ------ Verificar balance de Carlos ------
        # Carlos pagó $90 por supermercado (su parte: $30)
        # Carlos debe $40 por su parte de comida
        # Carlos debe $30 por su parte del cine
        # Carlos pagó $20 a Juan
        # Carlos recibió $15 de María
        # Total deuda: $40 + $30 = $70
        # Total recibido: $60 (de otros por supermercado) + $15 (pago de María) = $75
        # Neto: +$5
        carlos_balance = next(b for b in result if b.name == "Carlos Rodríguez")
        assert round(carlos_balance.total_debt, 2) == 70.0
        assert round(carlos_balance.total_owed, 2) == 75.0
        assert round(carlos_balance.net_balance, 2) == 5.0
        
        # Verificar que la suma de saldos netos es aproximadamente cero (puede haber pequeñas diferencias por redondeo)
        sum_net_balance = sum(b.net_balance for b in result)
        assert abs(sum_net_balance) < 0.01 