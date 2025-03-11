import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from app.models.models import Family, Member, Expense, Payment

class TestBase:
    """
    Clase base para las pruebas de servicios.
    
    Proporciona métodos comunes y configuraciones para las pruebas de los servicios.
    """
    
    @pytest.fixture
    def mock_db(self):
        """
        Fixture que proporciona una sesión de base de datos mock.
        
        Returns:
            MagicMock: Un mock de una sesión de SQLAlchemy
        """
        mock = MagicMock(spec=Session)
        return mock
    
    def setup_mock_query(self, mock_db, result_list=None, single_result=None):
        """
        Configura un mock para la función query de la base de datos.
        
        Args:
            mock_db: El mock de la sesión de base de datos
            result_list: Lista de resultados a devolver para el método all()
            single_result: Resultado único a devolver para el método first()
            
        Returns:
            MagicMock: El mock de la consulta configurado
        """
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        
        # Configurar filter y filter_by para devolver el mismo mock
        mock_query.filter.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        
        # Configurar join y options para devolver el mismo mock
        mock_query.join.return_value = mock_query
        mock_query.options.return_value = mock_query
        
        # Configurar el resultado de all()
        if result_list is not None:
            mock_query.all.return_value = result_list
        
        # Configurar el resultado de first()
        if single_result is not None:
            mock_query.first.return_value = single_result
        
        return mock_query
    
    def create_mock_member(self, id=None, name=None, telegram_id=None, family_id=None):
        """
        Crea un objeto Member mock.
        
        Args:
            id: ID del miembro
            name: Nombre del miembro
            telegram_id: ID de Telegram del miembro
            family_id: ID de la familia a la que pertenece
            
        Returns:
            MagicMock: Un mock de un miembro
        """
        mock_member = MagicMock(spec=Member)
        mock_member.id = id or "member-uuid-1"
        mock_member.name = name or "Test Member"
        mock_member.telegram_id = telegram_id or "123456789"
        mock_member.family_id = family_id or "family-uuid-1"
        return mock_member
    
    def create_mock_family(self, id=None, name=None, members=None):
        """
        Crea un objeto Family mock.
        
        Args:
            id: ID de la familia
            name: Nombre de la familia
            members: Lista de miembros de la familia
            
        Returns:
            MagicMock: Un mock de una familia
        """
        mock_family = MagicMock(spec=Family)
        mock_family.id = id or "family-uuid-1"
        mock_family.name = name or "Test Family"
        mock_family.members = members or []
        return mock_family
    
    def create_mock_expense(self, id=None, description=None, amount=None, paid_by=None, family_id=None, split_among=None):
        """
        Crea un objeto Expense mock.
        
        Args:
            id: ID del gasto
            description: Descripción del gasto
            amount: Monto del gasto
            paid_by: ID del miembro que pagó
            family_id: ID de la familia
            split_among: Lista de miembros entre los que se divide el gasto
            
        Returns:
            MagicMock: Un mock de un gasto
        """
        mock_expense = MagicMock(spec=Expense)
        mock_expense.id = id or "expense-uuid-1"
        mock_expense.description = description or "Test Expense"
        mock_expense.amount = amount or 100.0
        mock_expense.paid_by = paid_by or "member-uuid-1"
        mock_expense.family_id = family_id or "family-uuid-1"
        mock_expense.split_among = split_among or []
        return mock_expense
    
    def create_mock_payment(self, id=None, from_member_id=None, to_member_id=None, amount=None, family_id=None):
        """
        Crea un objeto Payment mock.
        
        Args:
            id: ID del pago
            from_member_id: ID del miembro que envía el pago
            to_member_id: ID del miembro que recibe el pago
            amount: Monto del pago
            family_id: ID de la familia
            
        Returns:
            MagicMock: Un mock de un pago
        """
        mock_payment = MagicMock(spec=Payment)
        mock_payment.id = id or "payment-uuid-1"
        mock_payment.from_member_id = from_member_id or "member-uuid-1"
        mock_payment.to_member_id = to_member_id or "member-uuid-2"
        mock_payment.amount = amount or 50.0
        mock_payment.family_id = family_id or "family-uuid-1"
        return mock_payment 