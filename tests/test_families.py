import pytest
from fastapi import status
from app.models.models import Family, Member
from app.auth.auth import create_access_token

def test_create_family(client):
    # Datos para crear una nueva familia
    family_data = {
        "name": "Nueva Familia",
        "members": [
            {"name": "Miembro 1", "telegram_id": "111111"},
            {"name": "Miembro 2", "telegram_id": "222222"}
        ]
    }
    
    # Crear la familia
    response = client.post(
        "/families/",
        json=family_data
    )
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verificar los datos de la familia creada
    data = response.json()
    assert data["name"] == "Nueva Familia"
    assert len(data["members"]) == 2
    assert data["members"][0]["name"] == "Miembro 1"
    assert data["members"][1]["name"] == "Miembro 2"

def test_get_family(client, test_db):
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
    
    # Crear un token de acceso para el miembro
    access_token = create_access_token(
        data={"sub": member.telegram_id}
    )
    
    # Obtener la familia
    response = client.get(
        f"/families/{family.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == status.HTTP_200_OK
    
    # Verificar los datos de la familia
    data = response.json()
    assert data["id"] == family.id
    assert data["name"] == "Familia de Prueba"

def test_get_family_members(client, test_db):
    # Crear una familia de prueba
    family = Family(name="Familia de Prueba")
    test_db.add(family)
    test_db.commit()
    test_db.refresh(family)
    
    # Crear miembros de prueba
    member1 = Member(
        name="Usuario 1",
        telegram_id="111111",
        family_id=family.id
    )
    member2 = Member(
        name="Usuario 2",
        telegram_id="222222",
        family_id=family.id
    )
    test_db.add(member1)
    test_db.add(member2)
    test_db.commit()
    
    # Crear un token de acceso para el miembro
    access_token = create_access_token(
        data={"sub": member1.telegram_id}
    )
    
    # Obtener los miembros de la familia
    response = client.get(
        f"/families/{family.id}/members",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == status.HTTP_200_OK
    
    # Verificar los datos de los miembros
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Usuario 1"
    assert data[1]["name"] == "Usuario 2" 