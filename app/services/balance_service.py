from sqlalchemy.orm import Session
from app.models.models import Family, Member, Expense, Payment
from app.models.schemas import MemberBalance, DebtDetail, CreditDetail
from typing import List, Dict

class BalanceService:
    """Servicio para calcular los balances de una familia."""
    
    @staticmethod
    def calculate_family_balances(db: Session, family_id: str) -> List[MemberBalance]:
        """Calcula los balances de todos los miembros de una familia."""
        # Obtener todos los miembros de la familia
        members = db.query(Member).filter(Member.family_id == family_id).all()
        member_ids = [m.id for m in members]
        
        # Inicializar el diccionario de balances
        balances: Dict[int, Dict] = {}
        for member in members:
            balances[member.id] = {
                "member_id": str(member.id),
                "name": member.name,
                "total_debt": 0.0,
                "total_owed": 0.0,
                "net_balance": 0.0,
                "debts": [],
                "credits": []
            }
        
        # Procesar los gastos
        expenses = db.query(Expense).filter(Expense.paid_by.in_(member_ids)).all()
        for expense in expenses:
            # Obtener el miembro que pagó
            payer_id = expense.paid_by
            
            # Obtener los miembros entre los que se divide el gasto
            split_members = expense.split_among
            
            # Si no hay miembros específicos, dividir entre todos
            if not split_members:
                split_members = members
            
            # Calcular el monto por miembro
            amount_per_member = expense.amount / len(split_members)
            
            # Actualizar los balances
            for member in split_members:
                # Si el miembro es el pagador, no se debe a sí mismo
                if member.id == payer_id:
                    continue
                
                # El miembro debe al pagador
                balances[member.id]["total_debt"] += amount_per_member
                balances[payer_id]["total_owed"] += amount_per_member
                
                # Añadir la deuda a la lista de deudas del miembro
                balances[member.id]["debts"].append({
                    "to": str(payer_id),
                    "amount": amount_per_member
                })
                
                # Añadir el crédito a la lista de créditos del pagador
                balances[payer_id]["credits"].append({
                    "from": str(member.id),
                    "amount": amount_per_member
                })
        
        # Procesar los pagos
        # Usar consultas separadas para from_member y to_member para evitar el uso de in_() en relaciones
        payments_from = db.query(Payment).filter(Payment.from_member_id.in_(member_ids)).all()
        payments_to = db.query(Payment).filter(Payment.to_member_id.in_(member_ids)).all()
        
        # Combinar los resultados
        payments = payments_from + payments_to
        
        for payment in payments:
            from_member_id = payment.from_member_id
            to_member_id = payment.to_member_id
            amount = payment.amount
            
            # Verificar que ambos miembros pertenecen a la familia
            if from_member_id in balances and to_member_id in balances:
                # Actualizar los balances
                balances[from_member_id]["total_debt"] -= amount
                balances[to_member_id]["total_owed"] -= amount
        
        # Calcular el balance neto para cada miembro
        for member_id, balance in balances.items():
            balance["net_balance"] = balance["total_owed"] - balance["total_debt"]
        
        # Convertir a lista de objetos MemberBalance
        result = []
        for member_id, balance_data in balances.items():
            member_balance = MemberBalance(
                member_id=balance_data["member_id"],
                name=balance_data["name"],
                total_debt=balance_data["total_debt"],
                total_owed=balance_data["total_owed"],
                net_balance=balance_data["net_balance"],
                debts=[DebtDetail(**debt) for debt in balance_data["debts"]],
                credits=[CreditDetail(**credit) for credit in balance_data["credits"]]
            )
            result.append(member_balance)
        
        return result
    
    @staticmethod
    def get_member_balance(db: Session, family_id: str, member_id: int) -> MemberBalance:
        """Obtiene el balance de un miembro específico."""
        # Calcular los balances de toda la familia
        family_balances = BalanceService.calculate_family_balances(db, family_id)
        
        # Buscar el balance del miembro específico
        for balance in family_balances:
            if balance.member_id == str(member_id):
                return balance
        
        return None 