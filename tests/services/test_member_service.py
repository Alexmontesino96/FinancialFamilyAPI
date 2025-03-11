import pytest
from unittest.mock import MagicMock
from app.services.member_service import MemberService
from app.models.schemas import MemberCreate, MemberUpdate
from .test_base import TestBase

class TestMemberService(TestBase):
    """
    Pruebas unitarias para el servicio de miembros.
    """
    
    def test_create_member(self, mock_db):
        """
        Prueba la creación de un miembro.
        """
        # Configurar el mock
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()
        
        # Crear un miembro de prueba
        member_data = MemberCreate(
            name="Juan Pérez",
            telegram_id="123456789",
            family_id="family-uuid-1"
        )
        
        # Ejecutar el método a probar
        result = MemberService.create_member(mock_db, member_data)
        
        # Verificar que se llamaron los métodos correctos
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verificar que el resultado tiene los datos correctos
        assert result.name == "Juan Pérez"
        assert result.telegram_id == "123456789"
        assert result.family_id == "family-uuid-1"
    
    def test_get_member(self, mock_db):
        """
        Prueba la obtención de un miembro por ID.
        """
        # Crear un miembro mock
        mock_member = self.create_mock_member(
            id="member-uuid-1",
            name="Juan Pérez",
            telegram_id="123456789",
            family_id="family-uuid-1"
        )
        
        # Configurar el mock para devolver el miembro
        self.setup_mock_query(mock_db, single_result=mock_member)
        
        # Ejecutar el método a probar
        result = MemberService.get_member(mock_db, "member-uuid-1")
        
        # Verificar que se realizó la consulta correcta
        mock_db.query.assert_called_once()
        
        # Verificar que el resultado es el esperado
        assert result == mock_member
    
    def test_get_member_by_telegram_id(self, mock_db):
        """
        Prueba la obtención de un miembro por ID de Telegram.
        """
        # Crear un miembro mock
        mock_member = self.create_mock_member(
            id="member-uuid-1",
            name="Juan Pérez",
            telegram_id="123456789",
            family_id="family-uuid-1"
        )
        
        # Configurar el mock para devolver el miembro
        self.setup_mock_query(mock_db, single_result=mock_member)
        
        # Ejecutar el método a probar
        result = MemberService.get_member_by_telegram_id(mock_db, "123456789")
        
        # Verificar que se realizó la consulta correcta
        mock_db.query.assert_called_once()
        
        # Verificar que el resultado es el esperado
        assert result == mock_member
    
    def test_update_member(self, mock_db):
        """
        Prueba la actualización de un miembro.
        """
        # Crear un miembro mock
        mock_member = self.create_mock_member(
            id="member-uuid-1",
            name="Juan Pérez",
            telegram_id="123456789",
            family_id="family-uuid-1"
        )
        
        # Configurar el mock para devolver el miembro
        self.setup_mock_query(mock_db, single_result=mock_member)
        
        # Datos de actualización
        update_data = MemberUpdate(name="Juan Pérez Actualizado")
        
        # Ejecutar el método a probar
        result = MemberService.update_member(mock_db, "member-uuid-1", update_data)
        
        # Verificar que se realizó la consulta correcta
        mock_db.query.assert_called_once()
        
        # Verificar que se llamó a commit
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verificar que el resultado es el esperado
        assert result == mock_member
    
    def test_delete_member(self, mock_db):
        """
        Prueba la eliminación de un miembro.
        """
        # Crear un miembro mock
        mock_member = self.create_mock_member(
            id="member-uuid-1",
            name="Juan Pérez",
            telegram_id="123456789",
            family_id="family-uuid-1"
        )
        
        # Configurar el mock para devolver el miembro
        self.setup_mock_query(mock_db, single_result=mock_member)
        
        # Ejecutar el método a probar
        result = MemberService.delete_member(mock_db, "member-uuid-1")
        
        # Verificar que se realizó la consulta correcta
        mock_db.query.assert_called_once()
        
        # Verificar que se llamó a delete y commit
        mock_db.delete.assert_called_once_with(mock_member)
        mock_db.commit.assert_called_once()
        
        # Verificar que el resultado es el esperado
        assert result == mock_member
    
    def test_get_member_not_found(self, mock_db):
        """
        Prueba que get_member devuelve None cuando no se encuentra el miembro.
        """
        # Configurar el mock para devolver None
        self.setup_mock_query(mock_db, single_result=None)
        
        # Ejecutar el método a probar
        result = MemberService.get_member(mock_db, "non-existent-uuid")
        
        # Verificar que se realizó la consulta correcta
        mock_db.query.assert_called_once()
        
        # Verificar que el resultado es None
        assert result is None 