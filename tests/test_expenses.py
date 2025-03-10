import pytest
from fastapi import status
from app.models.models import Family, Member, Expense
from app.auth.auth import create_access_token

def test_create_expense(client, test_db):
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
    test_db.refresh(member1)
    test_db.refresh(member2)
    
    # Crear un token de acceso para el miembro
    access_token = create_access_token(
        data={"sub": member1.telegram_id}
    )
    
    # Datos para crear un nuevo gasto
    expense_data = {
        "description": "Compra de comida",
        "amount": 100.50,
        "paid_by": member1.id,
        "split_among": [member1.id, member2.id]
    }
    
    # Crear el gasto
    response = client.post(
        "/expenses/",
        json=expense_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verificar los datos del gasto creado
    data = response.json()
    assert data["description"] == "Compra de comida"
    assert data["amount"] == 100.50
    assert data["paid_by"] == member1.id
    
def test_get_expense(client, test_db):
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
    
    # Crear un gasto de prueba
    expense = Expense(
        description="Gasto de prueba",
        amount=50.25,
        paid_by=member.id,
        family_id=family.id
    )
    test_db.add(expense)
    test_db.commit()
    test_db.refresh(expense)
    
    # Crear un token de acceso para el miembro
    access_token = create_access_token(
        data={"sub": member.telegram_id}
    )
    
    # Obtener el gasto
    response = client.get(
        f"/expenses/{expense.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == status.HTTP_200_OK
    
    # Verificar los datos del gasto
    data = response.json()
    assert data["id"] == expense.id
    assert data["description"] == "Gasto de prueba"
    assert data["amount"] == 50.25
    assert data["paid_by"] == member.id
    
def test_get_family_expenses(client, test_db):
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
    
    # Crear gastos de prueba
    expense1 = Expense(
        description="Gasto 1",
        amount=50.25,
        paid_by=member.id,
        family_id=family.id
    )
    expense2 = Expense(
        description="Gasto 2",
        amount=75.50,
        paid_by=member.id,
        family_id=family.id
    )
    test_db.add(expense1)
    test_db.add(expense2)
    test_db.commit()
    
    # Crear un token de acceso para el miembro
    access_token = create_access_token(
        data={"sub": member.telegram_id}
    )
    
    # Obtener los gastos de la familia
    response = client.get(
        f"/expenses/family/{family.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verificar que la respuesta sea exitosa
    assert response.status_code == status.HTTP_200_OK
    
    # Verificar los datos de los gastos
    data = response.json()
    assert len(data) == 2
    assert data[0]["description"] == "Gasto 1"
    assert data[1]["description"] == "Gasto 2" 