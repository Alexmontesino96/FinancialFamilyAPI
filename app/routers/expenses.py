"""
Expenses Router

This module defines the endpoints for managing expenses in the API.
It provides routes for creating, retrieving, updating, and deleting expenses,
as well as getting expenses by member or family.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.models.database import get_db
from app.models.schemas import Expense, ExpenseCreate, ExpenseUpdate
from app.services.expense_service import ExpenseService
from app.services.member_service import MemberService
from app.utils.logging_config import get_logger

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)

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
    logger.info(f"Request to create expense: {expense.description}, amount: {expense.amount}, paid_by: {expense.paid_by}")
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payer
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer:
            logger.warning(f"Member not found. Requesting member with telegram_id: {telegram_id} or payer with ID: {expense.paid_by}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
            
        if requesting_member.family_id != payer.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to create expense for member: {expense.paid_by}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create expenses for this member"
            )
    
    created_expense = ExpenseService.create_expense(db, expense)
    logger.info(f"Expense created successfully with ID: {created_expense.id}, family: {created_expense.family_id}")
    return created_expense

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
    logger.info(f"Request to get expense with ID: {expense_id}, requested by telegram_id: {telegram_id}")
    
    expense = ExpenseService.get_expense(db, expense_id)
    if not expense:
        logger.warning(f"Expense not found with ID: {expense_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payer
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer:
            logger.warning(f"Member not found. Requesting member with telegram_id: {telegram_id} or payer of expense: {expense_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
            
        if requesting_member.family_id != payer.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to view expense: {expense_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this expense"
            )
    
    logger.info(f"Expense retrieved successfully: {expense.id}, description: '{expense.description}'")
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
    logger.info(f"Request to update expense with ID: {expense_id}, requested by telegram_id: {telegram_id}")
    
    # Verify that the expense exists
    expense = ExpenseService.get_expense(db, expense_id)
    if not expense:
        logger.warning(f"Expense not found with ID: {expense_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payer
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer:
            logger.warning(f"Member not found. Requesting member with telegram_id: {telegram_id} or payer of expense: {expense_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
            
        if requesting_member.family_id != payer.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to update expense: {expense_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this expense"
            )
    
    # If the payer is changed, verify that the new payer belongs to the same family
    if expense_update.paid_by is not None and expense_update.paid_by != expense.paid_by:
        new_payer = MemberService.get_member(db, expense_update.paid_by)
        if not new_payer:
            logger.warning(f"New payer not found with ID: {expense_update.paid_by}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="New payer not found"
            )
            
        if new_payer.family_id != expense.family_id:
            logger.warning(f"Invalid payer update: New payer {expense_update.paid_by} belongs to family {new_payer.family_id}, but expense belongs to family {expense.family_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The new payer must belong to the same family"
            )
    
    # Update the expense
    updated_expense = ExpenseService.update_expense(db, expense_id, expense_update)
    if not updated_expense:
        logger.error(f"Error updating expense with ID: {expense_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error updating the expense"
        )
    
    logger.info(f"Expense updated successfully: {updated_expense.id}")
    return updated_expense

@router.get("/member/{member_id}", response_model=List[Expense])
def get_member_expenses(
    member_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get expenses for a specific member.
    
    Args:
        member_id (str): UUID of the member to get expenses for
        telegram_id: Optional Telegram ID for permission validation
        db: Database session
        
    Returns:
        List[Expense]: List of expenses for the member
        
    Raises:
        HTTPException: If the member is not found or the user doesn't have permission to view the expenses
    """
    logger.info(f"Request to get expenses for member: {member_id}, requested by telegram_id: {telegram_id}")
    
    member = MemberService.get_member(db, member_id)
    if not member:
        logger.warning(f"Member not found with ID: {member_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not requesting_member:
            logger.warning(f"Requesting member not found with telegram_id: {telegram_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requesting member not found"
            )
            
        if requesting_member.family_id != member.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to view expenses for member: {member_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this member's expenses"
            )
    
    expenses = ExpenseService.get_expenses_by_member(db, member_id)
    logger.info(f"Retrieved {len(expenses)} expenses for member: {member_id}")
    return expenses

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
    logger.info(f"Request to get expenses for family: {family_id}, requested by telegram_id: {telegram_id}")
    
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not member:
            logger.warning(f"Member not found with telegram_id: {telegram_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
            
        if member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to view expenses for family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this family's expenses"
            )
    
    expenses = ExpenseService.get_expenses_by_family(db, family_id)
    logger.info(f"Retrieved {len(expenses)} expenses for family: {family_id}")
    return expenses

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
    logger.info(f"Request to delete expense with ID: {expense_id}, requested by telegram_id: {telegram_id}")
    
    expense = ExpenseService.get_expense(db, expense_id)
    if not expense:
        logger.warning(f"Expense not found with ID: {expense_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the same family as the payer
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer:
            logger.warning(f"Member not found. Requesting member with telegram_id: {telegram_id} or payer of expense: {expense_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
            
        if requesting_member.family_id != payer.family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to delete expense: {expense_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this expense"
            )
    
    deleted_expense = ExpenseService.delete_expense(db, expense_id)
    logger.info(f"Expense deleted successfully: {expense_id}")
    return deleted_expense 