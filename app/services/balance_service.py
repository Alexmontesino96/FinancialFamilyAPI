from sqlalchemy.orm import Session
from app.models.models import Family, Member, Expense, Payment
from app.models.schemas import MemberBalance, DebtDetail, CreditDetail
from typing import List, Dict

class BalanceService:
    """
    Service for calculating family balances.
    
    This class provides methods for calculating the financial balances of family members,
    taking into account expenses and payments.
    """
    
    @staticmethod
    def calculate_family_balances(db: Session, family_id: str) -> List[MemberBalance]:
        """
        Calculate the balances of all members in a family.
        
        This method calculates how much each member owes or is owed by other members,
        based on expenses and payments.
        
        Args:
            db: Database session
            family_id: ID of the family to calculate balances for
            
        Returns:
            List[MemberBalance]: List of member balances with detailed debt and credit information
        """
        # Get all family members
        members = db.query(Member).filter(Member.family_id == family_id).all()
        member_ids = [m.id for m in members]
        
        # Initialize the balance dictionary
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
        
        # Process expenses
        expenses = db.query(Expense).filter(Expense.paid_by.in_(member_ids)).all()
        for expense in expenses:
            # Get the member who paid
            payer_id = expense.paid_by
            
            # Get the members among whom the expense is split
            split_members = expense.split_among
            
            # If no specific members, split among all
            if not split_members:
                split_members = members
            
            # Calculate the amount per member
            amount_per_member = expense.amount / len(split_members)
            
            # Update the balances
            for member in split_members:
                # If the member is the payer, they don't owe themselves
                if member.id == payer_id:
                    continue
                
                # The member owes the payer
                balances[member.id]["total_debt"] += amount_per_member
                balances[payer_id]["total_owed"] += amount_per_member
                
                # Add the debt to the member's debt list
                balances[member.id]["debts"].append({
                    "to": str(payer_id),
                    "amount": amount_per_member
                })
                
                # Add the credit to the payer's credit list
                balances[payer_id]["credits"].append({
                    "from": str(member.id),
                    "amount": amount_per_member
                })
        
        # Process payments
        # Use separate queries for from_member and to_member to avoid using in_() on relationships
        payments_from = db.query(Payment).filter(Payment.from_member_id.in_(member_ids)).all()
        payments_to = db.query(Payment).filter(Payment.to_member_id.in_(member_ids)).all()
        
        # Combine the results
        payments = payments_from + payments_to
        
        for payment in payments:
            from_member_id = payment.from_member_id
            to_member_id = payment.to_member_id
            amount = payment.amount
            
            # Verify that both members belong to the family
            if from_member_id in balances and to_member_id in balances:
                # Update the balances
                balances[from_member_id]["total_debt"] -= amount
                balances[to_member_id]["total_owed"] -= amount
        
        # Calculate the net balance for each member
        for member_id, balance in balances.items():
            balance["net_balance"] = balance["total_owed"] - balance["total_debt"]
        
        # Convert to a list of MemberBalance objects
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
        """
        Get the balance of a specific member.
        
        Args:
            db: Database session
            family_id: ID of the family the member belongs to
            member_id: ID of the member to get the balance for
            
        Returns:
            MemberBalance: The member's balance or None if not found
        """
        # Calculate the balances of the entire family
        family_balances = BalanceService.calculate_family_balances(db, family_id)
        
        # Find the balance of the specific member
        for balance in family_balances:
            if balance.member_id == str(member_id):
                return balance
        
        return None 