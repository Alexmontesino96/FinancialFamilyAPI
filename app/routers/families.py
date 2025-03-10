"""
Families Router

This module defines the endpoints for managing families in the API.
It provides routes for creating families, retrieving family information,
managing family members, and calculating balances.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import get_db
from app.models.schemas import Family, FamilyCreate, Member, MemberCreate
from app.services.family_service import FamilyService
from app.services.member_service import MemberService
from app.services.balance_service import BalanceService

router = APIRouter(
    prefix="/families",
    tags=["families"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Family, status_code=status.HTTP_201_CREATED)
def create_family(
    family: FamilyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new family.
    
    This endpoint creates a new family with the provided name and initial members.
    
    Args:
        family (FamilyCreate): Family data including name and initial members
        db (Session): Database session
    
    Returns:
        Family: The created family with its members
    
    Example:
        ```json
        {
          "name": "Smith Family",
          "members": [
            {
              "name": "John Smith",
              "telegram_id": "123456789"
            },
            {
              "name": "Jane Smith",
              "telegram_id": "987654321"
            }
          ]
        }
        ```
    """
    return FamilyService.create_family(db, family)

@router.get("/{family_id}", response_model=Family)
def get_family(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get family information.
    
    This endpoint retrieves information about a specific family.
    If a Telegram ID is provided, it verifies that the user belongs to the family.
    
    Args:
        family_id (str): ID of the family to retrieve
        telegram_id (Optional[str]): Telegram ID of the requesting user for authorization
        db (Session): Database session
    
    Returns:
        Family: The requested family with its members
    
    Raises:
        HTTPException: If the family is not found or the user doesn't have permission
    """
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this family"
            )
    
    family = FamilyService.get_family(db, family_id)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found"
        )
    return family

@router.get("/{family_id}/members", response_model=List[Member])
def get_family_members(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get family members.
    
    This endpoint retrieves all members of a specific family.
    If a Telegram ID is provided, it verifies that the user belongs to the family.
    
    Args:
        family_id (str): ID of the family
        telegram_id (Optional[str]): Telegram ID of the requesting user for authorization
        db (Session): Database session
    
    Returns:
        List[Member]: List of family members
    
    Raises:
        HTTPException: If the user doesn't have permission to access the family
    """
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this family"
            )
    
    return FamilyService.get_family_members(db, family_id)

@router.post("/{family_id}/members", response_model=Member, status_code=status.HTTP_201_CREATED)
def add_member_to_family(
    family_id: str,
    member: MemberCreate,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Add a member to a family.
    
    This endpoint adds a new member to an existing family.
    If a Telegram ID is provided, it verifies that the user belongs to the family.
    
    Args:
        family_id (str): ID of the family
        member (MemberCreate): Member data including name and Telegram ID
        telegram_id (Optional[str]): Telegram ID of the requesting user for authorization
        db (Session): Database session
    
    Returns:
        Member: The created member
    
    Raises:
        HTTPException: If the user doesn't have permission or the member already belongs to a family
    """
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        existing_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not existing_member or existing_member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this family"
            )
    
    # Check if the member already exists
    existing_member = MemberService.get_member_by_telegram_id(db, member.telegram_id)
    if existing_member:
        if existing_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This member already belongs to a family"
            )
    
    return FamilyService.add_member_to_family(db, family_id, member)

@router.get("/{family_id}/balances")
def get_family_balances(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get family balances.
    
    This endpoint calculates and retrieves the balance of all members in a family,
    showing who owes money to whom and how much.
    If a Telegram ID is provided, it verifies that the user belongs to the family.
    
    Args:
        family_id (str): ID of the family
        telegram_id (Optional[str]): Telegram ID of the requesting user for authorization
        db (Session): Database session
    
    Returns:
        List[MemberBalance]: List of member balances with detailed debt and credit information
    
    Raises:
        HTTPException: If the user doesn't have permission to access the family
    """
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this family"
            )
    
    return BalanceService.calculate_family_balances(db, family_id) 