"""
Payments Router

This module defines the endpoints for managing payments in the API.
It provides routes for creating, retrieving, and deleting payments,
as well as getting payments by member or family.
"""

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
    """
    # If a telegram_id is provided, verify that the user belongs to the same family as the payment members
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        from_member = MemberService.get_member(db, payment.from_member)
        to_member = MemberService.get_member(db, payment.to_member)
        
        if not requesting_member or not from_member or not to_member or requesting_member.family_id != from_member.family_id or from_member.family_id != to_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create payments for these members"
            )
    
    return PaymentService.create_payment(db, payment)

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