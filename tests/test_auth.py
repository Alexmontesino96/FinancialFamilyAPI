import pytest
from fastapi import status
from app.models.models import Member, Family

def test_create_access_token(client, test_db):
    # Crear una familia de prueba
    family = Family(name="Familia de Prueba")
    test_db.add(family)
    test_db.commit()
    test_db.refresh(family)
    
    # Crear un miembro de prueba
    member = Member(
        name="Usuario de Prueba",
        telegram_id="123456789",
        family_id=family.id
    )
    test_db.add(member)
    test_db.commit()
    test_db.refresh(member)
    
    # Intentar autenticar con el telegram_id
    response = client.post(
        "/auth/token",
        data={"username": "123456789", "password": ""}
    )
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == status.HTTP_200_OK
    
    # Verificar que la respuesta contenga un token de acceso
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
def test_invalid_authentication(client):
    # Intentar autenticar con un telegram_id que no existe
    response = client.post(
        "/auth/token",
        data={"username": "id_no_existente", "password": ""}
    )
    
    # Verificar que la respuesta sea un error de autenticación
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 