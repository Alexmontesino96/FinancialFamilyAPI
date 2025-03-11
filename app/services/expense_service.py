from sqlalchemy.orm import Session
from app.models.models import Expense, Member
from app.models.schemas import ExpenseCreate, ExpenseUpdate

class ExpenseService:
    """
    Service for managing expenses.
    
    This class provides methods for creating, retrieving, updating, and deleting
    expenses in the database, as well as retrieving expenses by member or family.
    """
    
    @staticmethod
    def create_expense(db: Session, expense: ExpenseCreate):
        """
        Create a new expense.
        
        Args:
            db: Database session
            expense: Expense data to create
            
        Returns:
            Expense: The created expense
            
        Note:
            If split_among is not specified, the expense is split among all family members.
        """
        # Create the expense without the split_among field first
        db_expense = Expense(
            description=expense.description,
            amount=expense.amount,
            paid_by=expense.paid_by
        )
        
        # Get the family of the paying member
        payer = db.query(Member).filter(Member.id == expense.paid_by).first()
        if payer:
            db_expense.family_id = payer.family_id
            
            # If split_among is not specified, split among all family members
            if not expense.split_among:
                # Get all family members
                family_members = db.query(Member).filter(Member.family_id == payer.family_id).all()
                db_expense.split_among = family_members
            else:
                # Use the specified members
                members = db.query(Member).filter(Member.id.in_(expense.split_among)).all()
                db_expense.split_among = members
        
        db.add(db_expense)
        db.commit()
        db.refresh(db_expense)
        return db_expense
    
    @staticmethod
    def get_expense(db: Session, expense_id: str):
        """
        Get an expense by its ID.
        
        Args:
            db: Database session
            expense_id: ID of the expense to retrieve
            
        Returns:
            Expense: The requested expense or None if not found
        """
        return db.query(Expense).filter(Expense.id == expense_id).first()
    
    @staticmethod
    def get_expenses_by_member(db: Session, member_id: str):
        """
        Get expenses paid by a member.
        
        Args:
            db: Database session
            member_id: ID of the member to get expenses for
            
        Returns:
            List[Expense]: List of expenses paid by the member
        """
        return db.query(Expense).filter(Expense.paid_by == member_id).all()
    
    @staticmethod
    def get_expenses_by_family(db: Session, family_id: str):
        """
        Get expenses for a family.
        
        Args:
            db: Database session
            family_id: ID of the family to get expenses for
            
        Returns:
            List[Expense]: List of expenses for the family
        """
        # Get the IDs of the family members
        member_ids = [m.id for m in db.query(Member).filter(Member.family_id == family_id).all()]
        
        # Get expenses where the payer is a family member
        return db.query(Expense).filter(Expense.paid_by.in_(member_ids)).all()
    
    @staticmethod
    def update_expense(db: Session, expense_id: str, expense_update: ExpenseUpdate):
        """
        Update an existing expense.
        
        Args:
            db: Database session
            expense_id: ID of the expense to update
            expense_update: Updated expense data
            
        Returns:
            Expense: The updated expense or None if not found
            
        Note:
            If split_among is set to an empty list, the expense is split among all family members.
            If the payer changes, the family_id is updated to match the new payer's family.
        """
        db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not db_expense:
            return None
        
        # Update the provided fields
        if expense_update.description is not None:
            db_expense.description = expense_update.description
        
        if expense_update.amount is not None:
            db_expense.amount = expense_update.amount
        
        if expense_update.paid_by is not None:
            db_expense.paid_by = expense_update.paid_by
            
            # Update the family if the payer changes
            payer = db.query(Member).filter(Member.id == expense_update.paid_by).first()
            if payer:
                db_expense.family_id = payer.family_id
        
        # Update split_among if provided
        if expense_update.split_among is not None:
            if not expense_update.split_among:
                # If the list is empty, split among all family members
                family_members = db.query(Member).filter(Member.family_id == db_expense.family_id).all()
                db_expense.split_among = family_members
            else:
                # Use the specified members
                members = db.query(Member).filter(Member.id.in_(expense_update.split_among)).all()
                db_expense.split_among = members
        
        db.commit()
        db.refresh(db_expense)
        return db_expense
    
    @staticmethod
    def delete_expense(db: Session, expense_id: str):
        """
        Delete an expense.
        
        Args:
            db: Database session
            expense_id: ID of the expense to delete
            
        Returns:
            Expense: The deleted expense or None if not found
        """
        db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if db_expense:
            db.delete(db_expense)
            db.commit()
        return db_expense 