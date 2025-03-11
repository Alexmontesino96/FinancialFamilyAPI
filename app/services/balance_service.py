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
        
        # Create a dictionary of members by ID for easy lookup
        members_by_id = {str(m.id): m for m in members}
        
        # Initialize the balance dictionary with string keys
        balances: Dict[str, Dict] = {}
        for member in members:
            balances[str(member.id)] = {
                "member_id": str(member.id),
                "name": member.name,
                "total_debt": 0.0,
                "total_owed": 0.0,
                "net_balance": 0.0,
                "debts_by_member": {},  # Dictionary to track debts by member
                "credits_by_member": {},  # Dictionary to track credits by member
                "debts": [],
                "credits": []
            }
        
        # Process expenses
        expenses = db.query(Expense).filter(Expense.paid_by.in_(member_ids)).all()
        for expense in expenses:
            # Get the member who paid
            payer_id = str(expense.paid_by)
            
            # Get the members among whom the expense is split
            split_members = expense.split_among
            
            # If no specific members, split among all
            if not split_members:
                split_members = members
            
            # Calculate the amount per member
            amount_per_member = expense.amount / len(split_members)
            
            # Update the balances
            for member in split_members:
                member_id = str(member.id)
                
                # If the member is the payer, they don't owe themselves
                if member_id == payer_id:
                    continue
                
                # Initialize the debt tracking for this pair if needed
                if payer_id not in balances[member_id]["debts_by_member"]:
                    balances[member_id]["debts_by_member"][payer_id] = 0.0
                
                if member_id not in balances[payer_id]["credits_by_member"]:
                    balances[payer_id]["credits_by_member"][member_id] = 0.0
                
                # Update the debt amount
                balances[member_id]["debts_by_member"][payer_id] += amount_per_member
                balances[payer_id]["credits_by_member"][member_id] += amount_per_member
                
                # Update totals
                balances[member_id]["total_debt"] += amount_per_member
                balances[payer_id]["total_owed"] += amount_per_member
        
        # Process payments
        payments_from = db.query(Payment).filter(Payment.from_member_id.in_(member_ids)).all()
        payments_to = db.query(Payment).filter(Payment.to_member_id.in_(member_ids)).all()
        
        # Combine the results
        payments = payments_from + payments_to
        
        for payment in payments:
            from_member_id = str(payment.from_member_id)
            to_member_id = str(payment.to_member_id)
            amount = payment.amount
            
            # Verify that both members belong to the family
            if from_member_id in balances and to_member_id in balances:
                # Update the debt tracking
                if to_member_id in balances[from_member_id]["debts_by_member"]:
                    # Reduce the debt, don't go below zero
                    current_debt = balances[from_member_id]["debts_by_member"][to_member_id]
                    reduction = min(current_debt, amount)
                    balances[from_member_id]["debts_by_member"][to_member_id] -= reduction
                    
                    # If debt is now zero, remove it entirely
                    if balances[from_member_id]["debts_by_member"][to_member_id] <= 0.001:  # Small threshold for float comparison
                        del balances[from_member_id]["debts_by_member"][to_member_id]
                
                # Update the credit tracking
                if from_member_id in balances[to_member_id]["credits_by_member"]:
                    # Reduce the credit, don't go below zero
                    current_credit = balances[to_member_id]["credits_by_member"][from_member_id]
                    reduction = min(current_credit, amount)
                    balances[to_member_id]["credits_by_member"][from_member_id] -= reduction
                    
                    # If credit is now zero, remove it entirely
                    if balances[to_member_id]["credits_by_member"][from_member_id] <= 0.001:  # Small threshold for float comparison
                        del balances[to_member_id]["credits_by_member"][from_member_id]
                
                # Update the totals
                balances[from_member_id]["total_debt"] -= amount
                balances[to_member_id]["total_owed"] -= amount
        
        # Convert the debt and credit dictionaries to lists
        for member_id, balance_data in balances.items():
            # Convert debts_by_member to debts list
            for to_id, amount in balance_data["debts_by_member"].items():
                if amount > 0:
                    debt_detail = {
                        "to": members_by_id[to_id].name,  # Use member name instead of ID
                        "amount": amount
                    }
                    balance_data["debts"].append(debt_detail)
            
            # Convert credits_by_member to credits list
            for from_id, amount in balance_data["credits_by_member"].items():
                if amount > 0:
                    credit_detail = {
                        "from": members_by_id[from_id].name,  # Use member name instead of ID
                        "amount": amount
                    }
                    balance_data["credits"].append(credit_detail)
            
            # Clean up temporary dictionaries
            del balance_data["debts_by_member"]
            del balance_data["credits_by_member"]
        
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
    def get_member_balance(db: Session, family_id: str, member_id: str) -> MemberBalance:
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