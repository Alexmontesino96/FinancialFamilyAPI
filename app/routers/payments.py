from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import get_db
from app.models.schemas import Payment, PaymentCreate
from app.services.payment_service import PaymentService
from app.services.member_service import MemberService

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Payment, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Crea un nuevo pago."""
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la misma familia que los miembros del pago
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        from_member = MemberService.get_member(db, payment.from_member)
        to_member = MemberService.get_member(db, payment.to_member)
        
        if not requesting_member or not from_member or not to_member or requesting_member.family_id != from_member.family_id or from_member.family_id != to_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear pagos para estos miembros"
            )
    
    return PaymentService.create_payment(db, payment)

@router.get("/{payment_id}", response_model=Payment)
def get_payment(
    payment_id: str,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene un pago por su ID."""
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la misma familia que los miembros del pago
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        from_member = MemberService.get_member(db, payment.from_member)
        to_member = MemberService.get_member(db, payment.to_member)
        
        if not requesting_member or not from_member or not to_member or requesting_member.family_id != from_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este pago"
            )
    
    return payment

@router.get("/member/{member_id}", response_model=List[Payment])
def get_member_payments(
    member_id: int,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene los pagos de un miembro."""
    member = MemberService.get_member(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la misma familia
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver los pagos de este miembro"
            )
    
    return PaymentService.get_payments_by_member(db, member_id)

@router.get("/family/{family_id}", response_model=List[Payment])
def get_family_payments(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene los pagos de una familia."""
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver los pagos de esta familia"
            )
    
    return PaymentService.get_payments_by_family(db, family_id)

@router.delete("/{payment_id}", response_model=Payment)
def delete_payment(
    payment_id: str,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Elimina un pago."""
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la misma familia que los miembros del pago
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        from_member = MemberService.get_member(db, payment.from_member)
        to_member = MemberService.get_member(db, payment.to_member)
        
        if not requesting_member or not from_member or not to_member or requesting_member.family_id != from_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar este pago"
            )
    
    return PaymentService.delete_payment(db, payment_id) 