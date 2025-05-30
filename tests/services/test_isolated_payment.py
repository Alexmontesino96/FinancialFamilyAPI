"""
Pruebas aisladas para el PaymentService.

Este módulo contiene pruebas unitarias para el servicio de pagos de la aplicación
real, utilizando mocks para aislar la lógica de negocio de la base de datos.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from fastapi import HTTPException

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Importar el servicio real
from app.services.payment_service import PaymentService
from app.models.models import Payment, Member
from app.models.schemas import PaymentCreate

class TestIsolatedPaymentService(unittest.TestCase):
    """
    Pruebas unitarias aisladas para el servicio de pagos.
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
    
    def test_create_payment(self):
        """
        Prueba la creación de un pago.
        """
        # Configurar el comportamiento del mock de base de datos
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.member1
        
        # Crear datos para el pago
        payment_data = PaymentCreate(
            from_member="member-1",
            to_member="member-2",
            amount=50.0
        )
        
        # Ejecutar el método a probar
        result = PaymentService.create_payment(self.mock_db, payment_data)
        
        # Verificar que se llamó a la base de datos para obtener el miembro
        self.mock_db.query.assert_called()
        
        # Verificar que se llamó a add y commit en la base de datos
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        
        # Verificar que el resultado tiene los datos correctos
        self.assertEqual(result.from_member_id, "member-1")
        self.assertEqual(result.to_member_id, "member-2")
        self.assertEqual(result.amount, 50.0)
        self.assertEqual(result.family_id, self.member1.family_id)
    
    def test_create_payment_with_family_id(self):
        """
        Prueba la creación de un pago especificando el family_id.
        """
        # Crear datos para el pago
        payment_data = PaymentCreate(
            from_member="member-1",
            to_member="member-2",
            amount=50.0
        )
        
        # Ejecutar el método a probar con family_id explícito
        result = PaymentService.create_payment(self.mock_db, payment_data, family_id="custom-family")
        
        # Verificar que no se llamó a la base de datos para obtener el miembro
        # (porque se proporcionó el family_id directamente)
        self.mock_db.query.assert_not_called()
        
        # Verificar que se llamó a add y commit en la base de datos
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()
        
        # Verificar que el resultado tiene los datos correctos, incluyendo el family_id proporcionado
        self.assertEqual(result.from_member_id, "member-1")
        self.assertEqual(result.to_member_id, "member-2")
        self.assertEqual(result.amount, 50.0)
        self.assertEqual(result.family_id, "custom-family")
    
    def test_get_payment(self):
        """
        Prueba la obtención de un pago por su ID.
        """
        # Crear un pago mock
        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = "payment-1"
        mock_payment.from_member_id = "member-1"
        mock_payment.to_member_id = "member-2"
        mock_payment.amount = 50.0
        mock_payment.family_id = "family-1"
        
        # Configurar el comportamiento del mock de base de datos
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        
        # Ejecutar el método a probar
        result = PaymentService.get_payment(self.mock_db, "payment-1")
        
        # Verificar que se llamó a la base de datos correctamente
        self.mock_db.query.assert_called_once()
        
        # Verificar que el resultado es el pago mock
        self.assertEqual(result, mock_payment)
    
    def test_get_payments_by_member(self):
        """
        Prueba la obtención de pagos relacionados con un miembro.
        """
        # Crear pagos mock
        mock_payment1 = MagicMock(spec=Payment)
        mock_payment1.id = "payment-1"
        mock_payment1.from_member_id = "member-1"
        mock_payment1.to_member_id = "member-2"
        
        mock_payment2 = MagicMock(spec=Payment)
        mock_payment2.id = "payment-2"
        mock_payment2.from_member_id = "member-2"
        mock_payment2.to_member_id = "member-1"
        
        # Configurar el comportamiento del mock de base de datos
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_payment1, mock_payment2]
        
        # Ejecutar el método a probar
        result = PaymentService.get_payments_by_member(self.mock_db, "member-1")
        
        # Verificar que se llamó a la base de datos correctamente
        self.mock_db.query.assert_called_once()
        
        # Verificar que el resultado contiene los pagos mock
        self.assertEqual(len(result), 2)
        self.assertIn(mock_payment1, result)
        self.assertIn(mock_payment2, result)
    
    def test_delete_payment(self):
        """
        Prueba la eliminación de un pago.
        """
        # Crear un pago mock
        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = "payment-1"
        
        # Configurar el comportamiento del mock de base de datos
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_payment
        
        # Ejecutar el método a probar
        result = PaymentService.delete_payment(self.mock_db, "payment-1")
        
        # Verificar que se llamó a la base de datos correctamente
        self.mock_db.query.assert_called_once()
        
        # Verificar que se llamó a delete y commit
        self.mock_db.delete.assert_called_once_with(mock_payment)
        self.mock_db.commit.assert_called_once()
        
        # Verificar que el resultado es el pago eliminado
        self.assertEqual(result, mock_payment)
    
    def test_delete_payment_not_found(self):
        """
        Prueba la eliminación de un pago que no existe.
        """
        # Configurar el comportamiento del mock de base de datos para devolver None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Ejecutar el método a probar
        result = PaymentService.delete_payment(self.mock_db, "non-existent-payment")
        
        # Verificar que se llamó a la base de datos correctamente
        self.mock_db.query.assert_called_once()
        
        # Verificar que no se llamó a delete ni commit
        self.mock_db.delete.assert_not_called()
        self.mock_db.commit.assert_not_called()
        
        # Verificar que el resultado es None
        self.assertIsNone(result)

    def test_payment_exceeding_debt(self):
        """
        Prueba que verifica que un pago no puede exceder la deuda actual.
        """
        # Configurar el mock de la base de datos
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.member1
        
        # Crear datos para el pago (monto mayor que la deuda)
        payment_data = PaymentCreate(
            from_member="member-1",
            to_member="member-2",
            amount=150.0  # Monto mayor que la deuda simulada
        )
        
        # Mock del BalanceService para simular una deuda de 100
        with patch('app.services.balance_service.BalanceService.calculate_family_balances') as mock_calculate:
            # Crear un balance mock para el pagador
            from app.models.schemas import MemberBalance, DebtDetail
            
            # Balance mock donde el pagador debe 100 al destinatario
            mock_balance = MemberBalance(
                member_id="member-1",
                name="Juan Pérez",
                total_debt=100.0,
                total_owed=0.0,
                net_balance=-100.0,
                debts=[
                    DebtDetail(to="María López", amount=100.0)
                ]
            )
            
            # Configurar el mock para devolver una lista con el balance del pagador
            mock_calculate.return_value = [mock_balance]
            
            # Verificar que se lanza la excepción apropiada
            with self.assertRaises(HTTPException) as context:
                PaymentService.create_payment(self.mock_db, payment_data, family_id="family-1")
            
            # Verificar los detalles de la excepción
            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("exceeds the debt", context.exception.detail)
            
            # Verificar que se llamó al método calculate_family_balances
            mock_calculate.assert_called_once_with(self.mock_db, "family-1")
            
            # Verificar que no se agregó ningún pago a la base de datos
            self.mock_db.add.assert_not_called()
            self.mock_db.commit.assert_not_called()

    def test_payment_equal_to_debt(self):
        """
        Prueba que verifica que un pago igual a la deuda actual es válido.
        """
        # Configurar el mock de la base de datos
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.member1
        
        # Crear datos para el pago (monto exactamente igual a la deuda)
        payment_data = PaymentCreate(
            from_member="member-1",
            to_member="member-2",
            amount=100.0  # Monto igual a la deuda simulada
        )
        
        # Mock del BalanceService para simular una deuda de 100
        with patch('app.services.balance_service.BalanceService.calculate_family_balances') as mock_calculate:
            # Crear un balance mock para el pagador
            from app.models.schemas import MemberBalance, DebtDetail
            
            # Balance mock donde el pagador debe 100 al destinatario
            mock_balance = MemberBalance(
                member_id="member-1",
                name="Juan Pérez",
                total_debt=100.0,
                total_owed=0.0,
                net_balance=-100.0,
                debts=[
                    DebtDetail(to="María López", amount=100.0)
                ]
            )
            
            # Configurar el mock para devolver una lista con el balance del pagador
            mock_calculate.return_value = [mock_balance]
            
            # Ejecutar el método a probar
            result = PaymentService.create_payment(self.mock_db, payment_data, family_id="family-1")
            
            # Verificar que se llamó al método calculate_family_balances
            mock_calculate.assert_called_once_with(self.mock_db, "family-1")
            
            # Verificar que se agregó el pago a la base de datos
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
            
            # Verificar que el resultado tiene los datos correctos
            self.assertEqual(result.from_member_id, "member-1")
            self.assertEqual(result.to_member_id, "member-2")
            self.assertEqual(result.amount, 100.0)
            self.assertEqual(result.family_id, "family-1")

    def test_payment_with_no_debt(self):
        """
        Prueba que verifica que un pago a alguien a quien no se le debe dinero es rechazado.
        """
        # Configurar el mock de la base de datos
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.member1
        
        # Crear datos para el pago
        payment_data = PaymentCreate(
            from_member="member-1",
            to_member="member-3",  # Un miembro diferente al que se le debe
            amount=50.0
        )
        
        # Mock del BalanceService para simular una deuda a otro miembro
        with patch('app.services.balance_service.BalanceService.calculate_family_balances') as mock_calculate:
            from app.models.schemas import MemberBalance, DebtDetail
            
            # Balance mock donde el pagador debe dinero a alguien más, pero no al destinatario
            mock_balance = MemberBalance(
                member_id="member-1",
                name="Juan Pérez",
                total_debt=100.0,
                total_owed=0.0,
                net_balance=-100.0,
                debts=[
                    DebtDetail(to="María López", amount=100.0)  # Debe a María, no al destinatario
                ]
            )
            
            # Configurar el mock para devolver una lista con el balance del pagador
            mock_calculate.return_value = [mock_balance]
            
            # Verificar que se lanza la excepción apropiada
            with self.assertRaises(HTTPException) as context:
                PaymentService.create_payment(self.mock_db, payment_data, family_id="family-1")
            
            # Verificar los detalles de la excepción
            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("No debt found", context.exception.detail)
            
            # Verificar que no se agregó ningún pago a la base de datos
            self.mock_db.add.assert_not_called()
            self.mock_db.commit.assert_not_called()

if __name__ == "__main__":
    unittest.main() 