from sqlalchemy.orm import Session
from app.models.models import Payment, Member
from app.models.schemas import PaymentCreate

class PaymentService:
    """Servicio para manejar los pagos."""
    
    @staticmethod
    def create_payment(db: Session, payment: PaymentCreate):
        """Crea un nuevo pago."""
        # Obtener la familia del miembro que paga
        from_member = db.query(Member).filter(Member.id == payment.from_member).first()
        
        db_payment = Payment(
            from_member_id=payment.from_member,
            to_member_id=payment.to_member,
            amount=payment.amount
        )
        
        # Asignar la familia del miembro que paga
        if from_member:
            db_payment.family_id = from_member.family_id
            
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment
    
    @staticmethod
    def get_payment(db: Session, payment_id: str):
        """Obtiene un pago por su ID."""
        return db.query(Payment).filter(Payment.id == payment_id).first()
    
    @staticmethod
    def get_payments_by_member(db: Session, member_id: int):
        """Obtiene los pagos realizados o recibidos por un miembro."""
        return db.query(Payment).filter(
            (Payment.from_member_id == member_id) | (Payment.to_member_id == member_id)
        ).all()
    
    @staticmethod
    def get_payments_by_family(db: Session, family_id: str):
        """Obtiene los pagos de una familia."""
        # Obtener los IDs de los miembros de la familia
        member_ids = [m.id for m in db.query(Member).filter(Member.family_id == family_id).all()]
        
        # Obtener los pagos donde el pagador o el receptor es un miembro de la familia
        return db.query(Payment).filter(
            (Payment.from_member_id.in_(member_ids)) | (Payment.to_member_id.in_(member_ids))
        ).all()
    
    @staticmethod
    def delete_payment(db: Session, payment_id: str):
        """Elimina un pago."""
        db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if db_payment:
            db.delete(db_payment)
            db.commit()
        return db_payment 