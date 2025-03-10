"""
Expenses Router

This module defines the endpoints for managing expenses in the API.
It provides routes for creating, retrieving, updating, and deleting expenses,
as well as getting expenses by member or family.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import get_db
from app.models.schemas import Expense, ExpenseCreate, ExpenseUpdate
from app.services.expense_service import ExpenseService
from app.services.member_service import MemberService

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Expense, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Create a new expense.
    
    Args:
        expense: Expense data to create
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Expense: The created expense
        
    Raises:
        HTTPException: If the user doesn't have permission to create expenses for this member
    """
    # If a telegram_id is provided, verify that the user belongs to the same family as the payer
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer or requesting_member.family_id != payer.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create expenses for this member"
            )
    
    return ExpenseService.create_expense(db, expense)

@router.get("/{expense_id}", response_model=Expense)
def get_expense(
    expense_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get an expense by its ID.
    
    Args:
        expense_id: ID of the expense to retrieve
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Expense: The requested expense
        
    Raises:
        HTTPException: If the expense is not found or the user doesn't have permission to view it
    """
    expense = ExpenseService.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payer
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer or requesting_member.family_id != payer.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this expense"
            )
    
    return expense

@router.put("/{expense_id}", response_model=Expense)
def update_expense(
    expense_id: str,
    expense_update: ExpenseUpdate,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Update an existing expense.
    
    Args:
        expense_id: ID of the expense to update
        expense_update: Updated expense data
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Expense: The updated expense
        
    Raises:
        HTTPException: If the expense is not found, the user doesn't have permission to update it,
                      or the new payer doesn't belong to the same family
    """
    # Verify that the expense exists
    expense = ExpenseService.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payer
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer or requesting_member.family_id != payer.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this expense"
            )
    
    # If the payer is changed, verify that the new payer belongs to the same family
    if expense_update.paid_by is not None and expense_update.paid_by != expense.paid_by:
        new_payer = MemberService.get_member(db, expense_update.paid_by)
        if not new_payer or new_payer.family_id != expense.family_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The new payer must belong to the same family"
            )
    
    # Update the expense
    updated_expense = ExpenseService.update_expense(db, expense_id, expense_update)
    if not updated_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error updating the expense"
        )
    
    return updated_expense

@router.get("/member/{member_id}", response_model=List[Expense])
def get_member_expenses(
    member_id: int,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get expenses for a specific member.
    
    Args:
        member_id: ID of the member to get expenses for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        List[Expense]: List of expenses for the member
        
    Raises:
        HTTPException: If the member is not found or the user doesn't have permission to view the expenses
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
                detail="You don't have permission to view this member's expenses"
            )
    
    return ExpenseService.get_expenses_by_member(db, member_id)

@router.get("/family/{family_id}", response_model=List[Expense])
def get_family_expenses(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get expenses for a specific family.
    
    Args:
        family_id: ID of the family to get expenses for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        List[Expense]: List of expenses for the family
        
    Raises:
        HTTPException: If the user doesn't have permission to view the family's expenses
    """
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this family's expenses"
            )
    
    return ExpenseService.get_expenses_by_family(db, family_id)

@router.delete("/{expense_id}", response_model=Expense)
def delete_expense(
    expense_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Delete an expense.
    
    Args:
        expense_id: ID of the expense to delete
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        Expense: The deleted expense
        
    Raises:
        HTTPException: If the expense is not found or the user doesn't have permission to delete it
    """
    expense = ExpenseService.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payer
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer or requesting_member.family_id != payer.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this expense"
            )
    
    return ExpenseService.delete_expense(db, expense_id) 