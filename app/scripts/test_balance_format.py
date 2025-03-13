"""
Script para probar el nuevo formato de balance con IDs de miembros.

Este script prueba que los balances se generan correctamente con los nuevos campos to_id y from_id.
"""

import json
from typing import Optional, List
from pydantic import BaseModel
from app.models.schemas import MemberBalance, DebtDetail, CreditDetail

def test_balance_format_offline():
    """
    Prueba el nuevo formato de balance sin conectarse a la base de datos.
    Crea modelos de balance simulados y verifica que los campos to_id y from_id estén presentes.
    """
    print("\n=== PRUEBA DEL NUEVO FORMATO DE BALANCES (OFFLINE) ===\n")
    
    try:
        # Crear ejemplos de deudas
        debts = [
            DebtDetail(to_id="2", to_name="María", amount=100.0),
            DebtDetail(to_id="3", to_name="Pedro", amount=50.0)
        ]
        
        # Crear ejemplos de créditos
        credits = [
            CreditDetail(from_id="1", from_name="Juan", amount=75.0),
            CreditDetail(from_id="4", from_name="Ana", amount=25.0)
        ]
        
        # Crear un balance de miembro simulado
        balance = MemberBalance(
            member_id="1",
            name="Juan",
            total_debt=150.0,
            total_owed=100.0,
            net_balance=-50.0,
            debts=debts,
            credits=credits
        )
        
        # Lista de balances simulados
        balances = [balance]
        
        # Convertir a JSON para verificar serialización
        # Para Pydantic v2, necesitamos usar model_dump
        json_str = json.dumps([b.model_dump(by_alias=True) for b in balances], indent=2)
        print("Ejemplo de respuesta de balance:")
        print(json_str)
        
        # Verificar que los campos to_id y from_id existen
        for member_balance in balances:
            for debt in member_balance.debts:
                assert hasattr(debt, 'to_id'), "El campo to_id no existe en DebtDetail"
                assert hasattr(debt, 'to_name'), "El campo to_name no existe en DebtDetail"
                print(f"✓ Deuda verificada: to_id={debt.to_id}, to_name={debt.to_name}, amount={debt.amount}")
            
            for credit in member_balance.credits:
                assert hasattr(credit, 'from_id'), "El campo from_id no existe en CreditDetail"
                assert hasattr(credit, 'from_name'), "El campo from_name no existe en CreditDetail"
                print(f"✓ Crédito verificado: from_id={credit.from_id}, from_name={credit.from_name}, amount={credit.amount}")
        
        # Verificar que la serialización funciona correctamente
        data = json.loads(json_str)
        
        # Verificar que los IDs están presentes en el JSON
        assert 'to_id' in data[0]['debts'][0], "El campo to_id no está en el JSON serializado"
        assert 'to' in data[0]['debts'][0], "El campo to (alias) no está en el JSON serializado"
        assert 'from_id' in data[0]['credits'][0], "El campo from_id no está en el JSON serializado"
        assert 'from' in data[0]['credits'][0], "El campo from (alias) no está en el JSON serializado"
        
        print("\n✅ PRUEBA EXITOSA: El nuevo formato de balance funciona correctamente.")
        return True
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_balance_format_offline():
        print("\nEl script de prueba ha verificado que los modelos de balance ahora incluyen IDs de miembros.")
        print("Esto resuelve el problema de ambigüedad cuando hay miembros con el mismo nombre.")
    else:
        print("\nLa prueba ha fallado. Por favor revise los modelos y la implementación.") 