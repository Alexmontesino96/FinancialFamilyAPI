"""
Pruebas aisladas para el PaymentService.

Este módulo contiene pruebas unitarias para el servicio de pagos de la aplicación
real, utilizando mocks para aislar la lógica de negocio de la base de datos.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

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

if __name__ == "__main__":
    unittest.main() 