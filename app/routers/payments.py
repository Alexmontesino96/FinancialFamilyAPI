"""
Payments Router

This module defines the endpoints for managing payments in the API.
It provides routes for creating, retrieving, and deleting payments,
as well as getting payments by member or family.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Tuple, Any
import logging

from app.models.database import get_db
from app.models.schemas import Payment, PaymentCreate, PaymentUpdate, PaymentStatus
from app.services.payment_service import PaymentService
from app.services.member_service import MemberService
from app.services.balance_service import BalanceService
from app.utils.logging_config import get_logger

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)

@router.post("/", response_model=Payment, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Create a new payment.
    
    Creates a payment between two members of a family. The payment is initially set to status PENDING
    and must be confirmed by the recipient before it affects balance calculations.
    
    Args:
        payment: Payment data to create (from_member, to_member, amount)
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Payment: The created payment with status PENDING
        
    Raises:
        HTTPException: If the user doesn't have permission to create payments for these members,
                     if the payment amount exceeds the debt, or if there is no debt in that direction
    """
    logger.info(f"Request to create payment: from {payment.from_member} to {payment.to_member}, amount: {payment.amount}")
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payment members
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        from_member = MemberService.get_member(db, payment.from_member)
        to_member = MemberService.get_member(db, payment.to_member)
        
        if not requesting_member or not from_member or not to_member or requesting_member.family_id != from_member.family_id or from_member.family_id != to_member.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to create payment for members: {payment.from_member}, {payment.to_member}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear pagos entre estos miembros"
            )
    
    try:
        # Intentar crear el pago - aquí se validará si el monto excede la deuda
        created_payment = PaymentService.create_payment(db, payment)
        logger.info(f"Payment created successfully with ID: {created_payment.id}")
        return created_payment
    except HTTPException as e:
        # Reenviar la excepción HTTP sin modificarla
        raise
    except Exception as e:
        # Para otros errores, enviar un mensaje genérico
        logger.error(f"Error al procesar el pago: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el pago: {str(e)}"
        )

@router.post("/debt-adjustment/", response_model=Payment, status_code=status.HTTP_201_CREATED)
def create_debt_adjustment(
    adjustment: PaymentCreate,
    telegram_id: Optional[str] = Query(None, description="Telegram ID del usuario"),
    db: Session = Depends(get_db)
):
    """
    Crea un ajuste de deuda.
    
    Permite a un miembro (acreedor) reducir parcialmente la deuda que 
    otro miembro (deudor) tiene hacia él. El ajuste de deuda se establece 
    directamente con estado CONFIRM, por lo que afecta inmediatamente
    a los cálculos de saldo sin requerir confirmación adicional.
    
    Args:
        adjustment: Datos del ajuste a crear (from_member, to_member, amount)
        telegram_id: ID de Telegram opcional para validación de permisos
        db: Sesión de base de datos
        
    Returns:
        Payment: El ajuste de deuda creado con estado CONFIRM
        
    Raises:
        HTTPException: Si el usuario no tiene permiso para crear ajustes para estos miembros,
                     si el monto del ajuste excede la deuda, o si no hay deuda en esa dirección
    """
    logger.info(f"Solicitud para crear ajuste de deuda: de {adjustment.from_member} a {adjustment.to_member}, monto: {adjustment.amount}")
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenezca a la misma familia que los miembros del ajuste
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        from_member = MemberService.get_member(db, adjustment.from_member)
        to_member = MemberService.get_member(db, adjustment.to_member)
        
        if not requesting_member or not from_member or not to_member or requesting_member.family_id != from_member.family_id or from_member.family_id != to_member.family_id:
            logger.warning(f"Permiso denegado para telegram_id: {telegram_id} para crear ajuste entre miembros: {adjustment.from_member}, {adjustment.to_member}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear ajustes de deuda entre estos miembros"
            )
    
    try:
        # Intentar crear el ajuste de deuda - aquí se validará si el monto excede la deuda
        created_adjustment = PaymentService.create_debt_adjustment(db, adjustment)
        logger.info(f"Ajuste de deuda creado exitosamente con ID: {created_adjustment.id}")
        return created_adjustment
    except HTTPException as e:
        # Reenviar la excepción HTTP sin modificarla
        raise
    except Exception as e:
        # Para otros errores, enviar un mensaje genérico
        logger.error(f"Error al procesar el ajuste de deuda: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el ajuste de deuda: {str(e)}"
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
    logger.info(f"Request to get payment with ID: {payment_id}, requested by telegram_id: {telegram_id}")
    
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        logger.warning(f"Payment not found with ID: {payment_id}")
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
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to view payment: {payment_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this payment"
            )
    
    logger.info(f"Payment retrieved successfully: {payment.id}")
    return payment

@router.get("/member/{member_id}", response_model=List[Payment])
def get_member_payments(
    member_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get regular payments for a specific member.
    
    Args:
        member_id: ID of the member to get payments for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        List[Payment]: List of regular payments involving the member
        
    Raises:
        HTTPException: If the member is not found or the user doesn't have permission to view the payments
    """
    logger.info(f"Request for member payments: member_id={member_id}, requested by telegram_id: {telegram_id}")
    
    # Get the member
    member = MemberService.get_member(db, member_id)
    if not member:
        logger.warning(f"Member not found: id={member_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != member.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to view payments for member: {member_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver los pagos de este miembro"
            )
    
    # Get the regular payments only
    payments = PaymentService.get_payments_by_member(db, member_id)
    logger.info(f"Returning {len(payments)} regular payments for member: {member_id}")
    return payments

@router.get("/member/{member_id}/adjustments", response_model=List[Payment])
def get_member_adjustments(
    member_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get debt adjustments for a specific member.
    
    Args:
        member_id: ID of the member to get debt adjustments for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        List[Payment]: List of debt adjustments involving the member
        
    Raises:
        HTTPException: If the member is not found or the user doesn't have permission to view the adjustments
    """
    logger.info(f"Request for member debt adjustments: member_id={member_id}, requested by telegram_id: {telegram_id}")
    
    # Get the member
    member = MemberService.get_member(db, member_id)
    if not member:
        logger.warning(f"Member not found: id={member_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != member.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to view adjustments for member: {member_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver los ajustes de deuda de este miembro"
            )
    
    # Get the debt adjustments
    adjustments = PaymentService.get_adjustments_by_member(db, member_id)
    logger.info(f"Returning {len(adjustments)} debt adjustments for member: {member_id}")
    return adjustments

@router.get("/family/{family_id}", response_model=List[Payment])
def get_family_payments(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get regular payments for a specific family.
    
    Args:
        family_id: ID of the family to get payments for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        List[Payment]: List of regular payments for the family
        
    Raises:
        HTTPException: If the user doesn't have permission to view the family's payments
    """
    logger.info(f"Request for family payments: family_id={family_id}, requested by telegram_id: {telegram_id}")
    
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to view payments for family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver los pagos de esta familia"
            )
    
    # Get regular payments only
    payments = PaymentService.get_payments_by_family(db, family_id)
    logger.info(f"Returning {len(payments)} regular payments for family: {family_id}")
    return payments

@router.get("/family/{family_id}/adjustments", response_model=List[Payment])
def get_family_adjustments(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get debt adjustments for a specific family.
    
    Args:
        family_id: ID of the family to get debt adjustments for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        List[Payment]: List of debt adjustments for the family
        
    Raises:
        HTTPException: If the user doesn't have permission to view the family's adjustments
    """
    logger.info(f"Request for family debt adjustments: family_id={family_id}, requested by telegram_id: {telegram_id}")
    
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to view adjustments for family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver los ajustes de deuda de esta familia"
            )
    
    # Get debt adjustments
    adjustments = PaymentService.get_adjustments_by_family(db, family_id)
    logger.info(f"Returning {len(adjustments)} debt adjustments for family: {family_id}")
    return adjustments

@router.delete("/{payment_id}", response_model=Dict[str, Any])
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
        Dict[str, Any]: A dictionary confirming the deletion and providing details.
        
    Raises:
        HTTPException: If the payment is not found or the user doesn't have permission to delete it
    """
    logger.info(f"Request to delete payment with ID: {payment_id}, requested by telegram_id: {telegram_id}")
    
    # We fetch the payment first mainly for permission checks
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        logger.warning(f"Payment not found with ID: {payment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payment members
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        # Need to ensure related members are loaded for permission check
        # This get_payment call might not load them eagerly, consider modifying if needed.
        # For now, assuming the loaded payment object has IDs accessible.
        if not requesting_member or not payment.family_id or requesting_member.family_id != payment.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to delete payment: {payment_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this payment"
            )
    
    # Call the service to delete the payment, which now returns a dict
    deleted_payment_data = PaymentService.delete_payment(db, payment_id)
    
    if deleted_payment_data:
        logger.info(f"Payment deleted successfully: {payment_id}")
        return {"status": "success", "message": "Payment deleted successfully", "deleted_payment": deleted_payment_data}
    else:
        # This case might not be reachable if get_payment already checked
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment could not be deleted or was not found"
        )

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
    logger.info(f"Request to diagnose payments for family: {family_id}, requested by telegram_id: {telegram_id}")
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to diagnose payments for family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para diagnosticar los pagos de esta familia"
            )
    
    # Obtener diagnóstico de pagos
    all_payments, duplicate_analysis = BalanceService.debug_payment_handling(db, family_id)
    
    # Verificar consistencia de balances
    consistency_check = BalanceService.verify_balance_consistency(db, family_id)
    
    logger.info(f"Retrieved {len(all_payments)} payments for family: {family_id}")
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
    logger.info(f"Request to fix payment duplicates for family: {family_id}, requested by telegram_id: {telegram_id}")
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member or requesting_member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to fix payment duplicates for family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para corregir los pagos de esta familia"
            )
    
    # Obtener diagnóstico de pagos
    all_payments, duplicate_analysis = BalanceService.debug_payment_handling(db, family_id)
    
    # Si no hay duplicados, informar
    if not duplicate_analysis:
        logger.info(f"No se encontraron pagos duplicados para corregir en family: {family_id}")
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
    
    logger.info(f"Se eliminaron {len(deleted_payments)} pagos duplicados en family: {family_id}")
    return {
        "status": f"Se eliminaron {len(deleted_payments)} pagos duplicados",
        "payments_deleted": deleted_payments
    }

@router.patch("/{payment_id}/status", response_model=Payment)
def update_payment_status(
    payment_id: str,
    payment_update: PaymentUpdate,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Update a payment's status manually.
    
    This endpoint allows direct updating of a payment's status to any valid status value.
    In most cases, it's better to use the specific /confirm and /reject endpoints instead
    as they include appropriate validations for state transitions.
    
    Note:
        - Only CONFIRM status payments are considered in balance calculations.
        - Changing status from PENDING to CONFIRM will affect balances.
        - Changing status to/from INACTIVE will not affect existing balances.
    
    Args:
        payment_id: ID of the payment to update
        payment_update: New status data
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Payment: The updated payment
        
    Raises:
        HTTPException: If the payment is not found or the user doesn't have permission
    """
    logger.info(f"Request to update payment with ID: {payment_id}, new status: {payment_update.status}, requested by telegram_id: {telegram_id}")
    
    # Verificar que el pago existe
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        logger.warning(f"Payment not found with ID: {payment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar permisos
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not requesting_member or requesting_member.family_id != payment.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to update payment: {payment_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar este pago"
            )
    
    # Actualizar el estado del pago
    updated_payment = PaymentService.update_payment_status(db, payment_id, payment_update)
    logger.info(f"Payment updated successfully: {payment_id}, new status: {payment_update.status}")
    return updated_payment

@router.post("/{payment_id}/confirm", response_model=Payment)
def confirm_payment(
    payment_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Confirm a payment by setting its status to CONFIRM.
    
    When a payment is confirmed, its status changes from PENDING to CONFIRM, and it will be
    considered in balance calculations. Only payments in PENDING status can be confirmed.
    The payment must be confirmed by the recipient or another member of the same family.
    
    Args:
        payment_id: ID of the payment to confirm
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Payment: The confirmed payment
        
    Raises:
        HTTPException: If the payment is not found, not in PENDING status,
                      or the user doesn't have permission
    """
    logger.info(f"Request to confirm payment with ID: {payment_id}, requested by telegram_id: {telegram_id}")
    
    # Verificar que el pago existe
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        logger.warning(f"Payment not found with ID: {payment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar permisos
    # Solo el receptor del pago o un miembro de la misma familia puede confirmar
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not requesting_member:
            logger.warning(f"Requesting member not found with telegram_id: {telegram_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que es el receptor del pago o un miembro de la misma familia
        if requesting_member.id != payment.to_member_id and requesting_member.family_id != payment.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to confirm payment: {payment_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para confirmar este pago"
            )
    
    # Confirmar el pago
    confirmed_payment = PaymentService.confirm_payment(db, payment_id)
    logger.info(f"Payment confirmed successfully: {payment_id}")
    return confirmed_payment

@router.post("/{payment_id}/reject", response_model=Payment)
def reject_payment(
    payment_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Reject a payment by setting its status to INACTIVE.
    
    When a payment is rejected, its status changes from PENDING to INACTIVE, and it will NOT
    be considered in balance calculations. Only payments in PENDING status can be rejected.
    The payment can be rejected by the recipient, the sender, or another member of the same family.
    
    Args:
        payment_id: ID of the payment to reject
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Payment: The rejected payment
        
    Raises:
        HTTPException: If the payment is not found, not in PENDING status,
                      or the user doesn't have permission
    """
    logger.info(f"Request to reject payment with ID: {payment_id}, requested by telegram_id: {telegram_id}")
    
    # Verificar que el pago existe
    payment = PaymentService.get_payment(db, payment_id)
    if not payment:
        logger.warning(f"Payment not found with ID: {payment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar permisos
    # Solo el receptor del pago o quien lo creó puede rechazarlo
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not requesting_member:
            logger.warning(f"Requesting member not found with telegram_id: {telegram_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que es el receptor del pago, quien lo creó, o un miembro de la misma familia
        if (requesting_member.id != payment.to_member_id and 
            requesting_member.id != payment.from_member_id and 
            requesting_member.family_id != payment.family_id):
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to reject payment: {payment_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para rechazar este pago"
            )
    
    # Rechazar el pago
    rejected_payment = PaymentService.reject_payment(db, payment_id)
    logger.info(f"Payment rejected successfully: {payment_id}")
    return rejected_payment 