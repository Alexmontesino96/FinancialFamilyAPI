from sqlalchemy.orm import Session
from app.models.models import Payment, Member
from app.models.schemas import PaymentCreate
from fastapi import HTTPException, status

class PaymentService:
    """
    Service for managing payments.
    
    This class provides methods for creating, retrieving, and deleting payments
    in the database, as well as retrieving payments by member or family.
    """
    
    @staticmethod
    def create_payment(db: Session, payment: PaymentCreate, family_id: str = None):
        """
        Create a new payment.
        
        Args:
            db: Database session
            payment: Payment data to create
            family_id: Optional family ID. If not provided, it will be obtained from the paying member.
            
        Returns:
            Payment: The created payment
            
        Note:
            If family_id is not provided, it is automatically set to the family of the paying member.
        """
        # Validate that payment amount doesn't exceed the debt
        from app.services.balance_service import BalanceService
        
        # Get the family if not provided
        if not family_id:
            from_member = db.query(Member).filter(Member.id == payment.from_member).first()
            if from_member:
                family_id = from_member.family_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Member not found"
                )
        
        # Calculate current balances to check debt
        balances = BalanceService.calculate_family_balances(db, family_id)
        
        # Find the balance for the member making the payment
        payer_balance = next((b for b in balances if b.member_id == payment.from_member), None)
        
        if not payer_balance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payer not found in family balances"
            )
        
        # Check if the payer owes money to the recipient
        recipient_name = None
        debt_amount = 0.0
        
        # Find the debt to the recipient
        for debt in payer_balance.debts:
            # Get the recipient member to match the name
            recipient = db.query(Member).filter(Member.id == payment.to_member).first()
            if not recipient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Recipient not found"
                )
            
            if debt.to == recipient.name:
                debt_amount = debt.amount
                recipient_name = recipient.name
                break
        
        # If no debt found or payment exceeds debt
        if recipient_name is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No debt found from {payer_balance.name} to the recipient"
            )
        
        if payment.amount > debt_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment amount (${payment.amount:.2f}) exceeds the debt (${debt_amount:.2f})"
            )
        
        # Create the payment
        db_payment = Payment(
            from_member_id=payment.from_member,
            to_member_id=payment.to_member,
            amount=payment.amount
        )
        
        # Use provided family_id or get it from the paying member
        if family_id:
            db_payment.family_id = family_id
        
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment
    
    @staticmethod
    def get_payment(db: Session, payment_id: str):
        """
        Get a payment by its ID.
        
        Args:
            db: Database session
            payment_id: ID of the payment to retrieve
            
        Returns:
            Payment: The requested payment or None if not found
        """
        return db.query(Payment).filter(Payment.id == payment_id).first()
    
    @staticmethod
    def get_payments_by_member(db: Session, member_id: str):
        """
        Get all payments involving a specific member (sent or received).
        
        Args:
            db: Database session
            member_id: ID of the member
            
        Returns:
            List[Payment]: List of payments involving the member
        """
        return db.query(Payment).filter(
            (Payment.from_member_id == member_id) | (Payment.to_member_id == member_id)
        ).all()
    
    @staticmethod
    def get_payments_by_family(db: Session, family_id: str):
        """
        Get payments for a family.
        
        Args:
            db: Database session
            family_id: ID of the family to get payments for
            
        Returns:
            List[Payment]: List of payments for the family
        """
        # Get the IDs of the family members
        member_ids = [m.id for m in db.query(Member).filter(Member.family_id == family_id).all()]
        
        # Get payments where the payer or receiver is a family member
        return db.query(Payment).filter(
            (Payment.from_member_id.in_(member_ids)) | (Payment.to_member_id.in_(member_ids))
        ).all()
    
    @staticmethod
    def delete_payment(db: Session, payment_id: str):
        """
        Delete a payment.
        
        Args:
            db: Database session
            payment_id: ID of the payment to delete
            
        Returns:
            Payment: The deleted payment or None if not found
        """
        db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if db_payment:
            db.delete(db_payment)
            db.commit()
        return db_payment 