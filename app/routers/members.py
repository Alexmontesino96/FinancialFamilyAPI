"""
Members Router

This module defines the endpoints for managing members in the API.
It provides routes for retrieving, updating, and deleting members,
as well as getting member balances.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import get_db
from app.models.schemas import Member, MemberCreate, MemberBalance, MemberUpdate
from app.services.member_service import MemberService
from app.services.balance_service import BalanceService

router = APIRouter(
    prefix="/members",
    tags=["members"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{telegram_id}", response_model=Member)
def get_member_by_telegram_id(
    telegram_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a member by Telegram ID.
    
    This endpoint retrieves a member using their Telegram ID.
    
    Args:
        telegram_id (str): Telegram ID of the member to retrieve
        db (Session): Database session
    
    Returns:
        Member: The requested member
    
    Raises:
        HTTPException: If the member is not found
    """
    member = MemberService.get_member_by_telegram_id(db, telegram_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    return member

@router.get("/id/{member_id}", response_model=Member)
def get_member_by_id(
    member_id: int,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get a member by ID.
    
    This endpoint retrieves a member using their numeric ID.
    If a Telegram ID is provided, it verifies that the user belongs to the same family.
    
    Args:
        member_id (int): ID of the member to retrieve
        telegram_id (Optional[str]): Telegram ID of the requesting user for authorization
        db (Session): Database session
    
    Returns:
        Member: The requested member
    
    Raises:
        HTTPException: If the member is not found or the user doesn't have permission
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
                detail="You don't have permission to access this member"
            )
    
    return member

@router.get("/me/balance", response_model=MemberBalance)
def get_current_member_balance(
    telegram_id: str = Query(..., description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get the current member's balance.
    
    This endpoint calculates and retrieves the balance of the member identified by the provided Telegram ID,
    showing debts and credits with other family members.
    
    Args:
        telegram_id (str): Telegram ID of the member
        db (Session): Database session
    
    Returns:
        MemberBalance: Balance information including debts and credits
    
    Raises:
        HTTPException: If the member is not found or doesn't belong to a family
    """
    member = MemberService.get_member_by_telegram_id(db, telegram_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    if not member.family_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Member doesn't belong to any family"
        )
    
    return BalanceService.get_member_balance(db, member.family_id, member.id)

@router.put("/{member_id}", response_model=Member)
def update_member(
    member_id: int,
    member: MemberUpdate,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Update a member.
    
    This endpoint updates a member's information.
    If a Telegram ID is provided, it verifies that the user is the same member or belongs to the same family.
    
    Args:
        member_id (int): ID of the member to update
        member (MemberUpdate): Updated member data
        telegram_id (Optional[str]): Telegram ID of the requesting user for authorization
        db (Session): Database session
    
    Returns:
        Member: The updated member
    
    Raises:
        HTTPException: If the member is not found or the user doesn't have permission
    """
    db_member = MemberService.get_member(db, member_id)
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # If a telegram_id is provided, verify that the user is the same member or belongs to the same family
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not requesting_member or (requesting_member.id != member_id and requesting_member.family_id != db_member.family_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this member"
            )
    
    return MemberService.update_member(db, member_id, member)

@router.delete("/{member_id}", response_model=Member)
def delete_member(
    member_id: int,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Delete a member.
    
    This endpoint deletes a member from the system.
    If a Telegram ID is provided, it verifies that the user belongs to the same family.
    
    Args:
        member_id (int): ID of the member to delete
        telegram_id (Optional[str]): Telegram ID of the requesting user for authorization
        db (Session): Database session
    
    Returns:
        Member: The deleted member
    
    Raises:
        HTTPException: If the member is not found or the user doesn't have permission
    """
    # Verify that the member to delete exists
    db_member = MemberService.get_member(db, member_id)
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not requesting_member or requesting_member.family_id != db_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this member"
            )
    
    return MemberService.delete_member(db, member_id)

@router.get("/balance/{member_id}", response_model=MemberBalance)
def get_member_balance(
    member_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get the financial balance of a member.
    
    This endpoint calculates how much the member owes to others and how much others owe to them.
    
    Args:
        member_id: ID of the member to get the balance for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        MemberBalance: The member's financial balance
        
    Raises:
        HTTPException: If the member is not found or the user doesn't have permission to view the balance
    """
    # Get the member
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
                detail="You don't have permission to view this member's balance"
            )
    
    # Get the member's balance
    balance = BalanceService.get_member_balance(db, member.family_id, member_id)
    
    # Mejorar la visualización de los balances
    if not balance.debts:
        # Si el miembro no tiene deudas, añadir un mensaje
        balance.debts = []  # Asegurar que sea una lista vacía
    
    if not balance.credits:
        # Si nadie le debe al miembro, añadir un mensaje
        balance.credits = []  # Asegurar que sea una lista vacía
    
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found"
        )
    
    return balance 