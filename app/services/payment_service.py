from sqlalchemy.orm import Session
from app.models.models import Payment, Member, PaymentStatus
from app.models.schemas import PaymentCreate, PaymentUpdate
from fastapi import HTTPException, status
import logging

# Configurar logging
logger = logging.getLogger(__name__)

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
            The payment status is initially set to PENDING.
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
        
        # Obtener información sobre los miembros involucrados
        from_member = db.query(Member).filter(Member.id == payment.from_member).first()
        to_member = db.query(Member).filter(Member.id == payment.to_member).first()
        
        if not from_member or not to_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both members not found"
            )
            
        logger.info(f"Validando pago de {from_member.name} a {to_member.name} por ${payment.amount:.2f}")
        
        # Calculate current balances to check debt (con modo debug para cálculos precisos)
        balances = BalanceService.calculate_family_balances(db, family_id, debug_mode=True)
        
        # Find the balance for the member making the payment
        payer_balance = next((b for b in balances if b.member_id == payment.from_member), None)
        
        if not payer_balance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payer not found in family balances"
            )
        
        # Check if the payer owes money to the recipient
        recipient_name = to_member.name
        debt_amount = 0.0
        
        # Find the debt to the recipient
        for debt in payer_balance.debts:
            if debt.to_name == recipient_name:
                debt_amount = debt.amount
                break
        
        # Si no hay deuda directa, verificar si hay una deuda indirecta en la dirección contraria
        if debt_amount == 0:
            # Verificar si el receptor debe dinero al pagador (caso en que el pago sería excesivo)
            recipient_balance = next((b for b in balances if b.member_id == payment.to_member), None)
            
            if recipient_balance:
                # Verificar si el receptor tiene deudas con el pagador
                for debt in recipient_balance.debts:
                    if debt.to_name == from_member.name:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"El receptor {recipient_name} debe ${debt.amount:.2f} al pagador {from_member.name}. No puedes realizar un pago en esta dirección."
                        )
        
        # Si no hay deuda en ninguna dirección
        if debt_amount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No hay deuda pendiente de {from_member.name} hacia {recipient_name}"
            )
        
        # Verificar si el pago excede la deuda
        if payment.amount > debt_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El monto del pago (${payment.amount:.2f}) excede la deuda actual (${debt_amount:.2f})"
            )
        
        logger.info(f"Pago validado: ${payment.amount:.2f} de {from_member.name} a {recipient_name}, deuda actual: ${debt_amount:.2f}")
        
        # Create the payment
        db_payment = Payment(
            from_member_id=payment.from_member,
            to_member_id=payment.to_member,
            amount=payment.amount
            # status se establecerá al valor predeterminado (CONFIRM) de la base de datos
        )
        
        # Use provided family_id or get it from the paying member
        if family_id:
            db_payment.family_id = family_id
        
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment
    
    @staticmethod
    def update_payment_status(db: Session, payment_id: str, payment_update: PaymentUpdate):
        """
        Update a payment's status.
        
        Args:
            db: Database session
            payment_id: ID of the payment to update
            payment_update: New status data
            
        Returns:
            Payment: The updated payment
            
        Raises:
            HTTPException: If the payment is not found
        """
        db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not db_payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pago no encontrado"
            )
        
        # Actualizar el estado del pago
        db_payment.status = payment_update.status
        
        db.commit()
        db.refresh(db_payment)
        return db_payment
    
    @staticmethod
    def confirm_payment(db: Session, payment_id: str):
        """
        Confirm a payment by changing its status to CONFIRM.
        
        Args:
            db: Database session
            payment_id: ID of the payment to confirm
            
        Returns:
            Payment: The confirmed payment
            
        Raises:
            HTTPException: If the payment is not found or not in PENDING status
        """
        db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not db_payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pago no encontrado"
            )
        
        if db_payment.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El pago no puede ser confirmado porque su estado actual es {db_payment.status.value}"
            )
        
        # Actualizar el estado del pago a CONFIRM
        db_payment.status = PaymentStatus.CONFIRM
        
        db.commit()
        db.refresh(db_payment)
        return db_payment
    
    @staticmethod
    def reject_payment(db: Session, payment_id: str):
        """
        Reject a payment by changing its status to INACTIVE.
        
        Args:
            db: Database session
            payment_id: ID of the payment to reject
            
        Returns:
            Payment: The rejected payment
            
        Raises:
            HTTPException: If the payment is not found or not in PENDING status
        """
        db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not db_payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pago no encontrado"
            )
        
        if db_payment.status != PaymentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El pago no puede ser rechazado porque su estado actual es {db_payment.status.value}"
            )
        
        # Actualizar el estado del pago a INACTIVE
        db_payment.status = PaymentStatus.INACTIVE
        
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