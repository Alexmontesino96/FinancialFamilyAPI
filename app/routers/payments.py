"""
Payments Router

This module defines the endpoints for managing payments in the API.
It provides routes for creating, retrieving, and deleting payments,
as well as getting payments by member or family.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Tuple, Any

from app.models.database import get_db
from app.models.schemas import Payment, PaymentCreate
from app.services.payment_service import PaymentService
from app.services.member_service import MemberService
from app.services.balance_service import BalanceService

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Payment, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Create a new payment.
    
    Args:
        payment: Payment data to create
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Payment: The created payment
        
    Raises:
        HTTPException: If the user doesn't have permission to create payments for these members
                     or if the payment amount exceeds the debt
    """
    # If a telegram_id is provided, verify that the user belongs to the same family as the payment members
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        from_member = MemberService.get_member(db, payment.from_member)
        to_member = MemberService.get_member(db, payment.to_member)
        
        if not requesting_member or not from_member or not to_member or requesting_member.family_id != from_member.family_id or from_member.family_id != to_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear pagos entre estos miembros"
            )
    
    try:
        # Intentar crear el pago - aquí se validará si el monto excede la deuda
        return PaymentService.create_payment(db, payment)
    except HTTPException as e:
        # Reenviar la excepción HTTP sin modificarla
        raise
    except Exception as e:
        # Para otros errores, enviar un mensaje genérico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el pago: {str(e)}"
        )

@router.get("/{payment_id}", response_model=Payment)
def get_payment(
    payment_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get a payment by its ID.
    
    Args:
        payment_id: ID of the payment to retrieve
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Payment: The requested payment
        
    Raises:
        HTTPException: If the payment is not found or the user doesn't have permission to view it
    """
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payment members
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        from_member = MemberService.get_member(db, payment.from_member)
        to_member = MemberService.get_member(db, payment.to_member)
        
        if not requesting_member or not from_member or not to_member or requesting_member.family_id != from_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this payment"
            )
    
    return payment

@router.get("/member/{member_id}", response_model=List[Payment])
def get_member_payments(
    member_id: int,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get payments for a specific member.
    
    Args:
        member_id: ID of the member to get payments for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        List[Payment]: List of payments involving the member
        
    Raises:
        HTTPException: If the member is not found or the user doesn't have permission to view the payments
    """
    member = MemberService.get_member(db, member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this member's payments"
            )
    
    return PaymentService.get_payments_by_member(db, member_id)

@router.get("/family/{family_id}", response_model=List[Payment])
def get_family_payments(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get payments for a specific family.
    
    Args:
        family_id: ID of the family to get payments for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        List[Payment]: List of payments for the family
        
    Raises:
        HTTPException: If the user doesn't have permission to view the family's payments
    """
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this family's payments"
            )
    
    return PaymentService.get_payments_by_family(db, family_id)

@router.delete("/{payment_id}", response_model=Payment)
def delete_payment(
    payment_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Delete a payment.
    
    Args:
        payment_id: ID of the payment to delete
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Payment: The deleted payment
        
    Raises:
        HTTPException: If the payment is not found or the user doesn't have permission to delete it
    """
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payment members
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        from_member = MemberService.get_member(db, payment.from_member)
        to_member = MemberService.get_member(db, payment.to_member)
        
        if not requesting_member or not from_member or not to_member or requesting_member.family_id != from_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this payment"
            )
    
    return PaymentService.delete_payment(db, payment_id)

@router.get("/diagnostics/{family_id}", response_model=Dict[str, Any])
def diagnose_payment_issues(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Diagnostica problemas con los pagos en una familia.
    
    Args:
        family_id: ID de la familia a diagnosticar
        telegram_id: ID de Telegram opcional para validación de permisos
        db: Sesión de base de datos
        
    Returns:
        Dict: Información de diagnóstico que incluye:
            - all_payments: Lista de todos los pagos en la familia
            - possible_duplicates: Lista de posibles pagos duplicados
            - consistency_check: Si los balances son consistentes (suman cero)
    """
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para diagnosticar los pagos de esta familia"
            )
    
    # Obtener diagnóstico de pagos
    all_payments, duplicate_analysis = BalanceService.debug_payment_handling(db, family_id)
    
    # Verificar consistencia de balances
    consistency_check = BalanceService.verify_balance_consistency(db, family_id)
    
    return {
        "all_payments": all_payments,
        "possible_duplicates": duplicate_analysis,
        "consistency_check": consistency_check,
        "recommendation": "Si hay pagos duplicados, considera eliminarlos usando el endpoint DELETE /payments/{payment_id}"
    }

@router.post("/fix-duplicates/{family_id}", response_model=Dict[str, Any])
def fix_payment_duplicates(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Corrige automáticamente pagos duplicados en una familia.
    
    Este endpoint detecta pagos que parecen ser duplicados (mismo monto, mismo origen y destino)
    y elimina todos excepto el más reciente.
    
    Args:
        family_id: ID de la familia a corregir
        telegram_id: ID de Telegram opcional para validación de permisos
        db: Sesión de base de datos
        
    Returns:
        Dict: Información sobre las correcciones realizadas
    """
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para corregir los pagos de esta familia"
            )
    
    # Obtener diagnóstico de pagos
    all_payments, duplicate_analysis = BalanceService.debug_payment_handling(db, family_id)
    
    # Si no hay duplicados, informar
    if not duplicate_analysis:
        return {
            "status": "No se encontraron pagos duplicados para corregir",
            "payments_deleted": []
        }
    
    # Agrupar pagos por la "firma" (origen, destino, monto)
    payments_by_signature = {}
    for payment in all_payments:
        signature = f"{payment['from_member']}->{payment['to_member']}-{payment['amount']}"
        
        if signature not in payments_by_signature:
            payments_by_signature[signature] = []
        
        payments_by_signature[signature].append({
            "id": payment["id"],
            "created_at": payment["created_at"]
        })
    
    # Para cada grupo de pagos duplicados, mantener solo el más reciente
    deleted_payments = []
    for signature, payments in payments_by_signature.items():
        if len(payments) <= 1:
            continue  # No es un duplicado
        
        # Ordenar por fecha de creación (del más reciente al más antiguo)
        sorted_payments = sorted(payments, key=lambda p: p["created_at"], reverse=True)
        
        # Mantener el más reciente, eliminar el resto
        for payment in sorted_payments[1:]:
            deleted_payment = PaymentService.delete_payment(db, payment["id"])
            if deleted_payment:
                deleted_payments.append({
                    "id": deleted_payment.id,
                    "from_member_id": deleted_payment.from_member_id,
                    "to_member_id": deleted_payment.to_member_id,
                    "amount": deleted_payment.amount
                })
    
    return {
        "status": f"Se eliminaron {len(deleted_payments)} pagos duplicados",
        "payments_deleted": deleted_payments
    } 