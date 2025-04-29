"""
Families Router

This module defines the endpoints for managing families in the API.
It provides routes for creating families, retrieving family information,
managing family members, and calculating balances.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.models.database import get_db
from app.models.schemas import Family, FamilyCreate, Member, MemberCreate, MemberBalance
from app.services.family_service import FamilyService
from app.services.member_service import MemberService
from app.services.balance_service import BalanceService
from app.utils.logging_config import get_logger

router = APIRouter(
    prefix="/families",
    tags=["families"],
    responses={404: {"description": "Not found"}},
)

logger = get_logger(__name__)

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
    logger.info(f"Request to create family: '{family.name}' with {len(family.members)} initial members")
    created_family = FamilyService.create_family(db, family)
    logger.info(f"Family created successfully with ID: {created_family.id}, name: '{created_family.name}'")
    return created_family

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
    logger.info(f"Request to get family with ID: {family_id}, requested by telegram_id: {telegram_id}")
    
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not member or member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to access family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this family"
            )
    
    family = FamilyService.get_family(db, family_id)
    if not family:
        logger.warning(f"Family not found with ID: {family_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found"
        )
    
    logger.info(f"Family retrieved successfully: {family.id}, name: '{family.name}'")
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
    logger.info(f"Request to get members for family ID: {family_id}, requested by telegram_id: {telegram_id}")
    
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not member or member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to access family members: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this family"
            )
    
    members = FamilyService.get_family_members(db, family_id)
    logger.info(f"Retrieved {len(members)} members for family: {family_id}")
    return members

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
    logger.info(f"Request to add member: '{member.name}' with telegram_id: {member.telegram_id} to family: {family_id}")
    
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        existing_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not existing_member or existing_member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to add member to family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this family"
            )
    
    # Check if the member already exists
    existing_member = MemberService.get_member_by_telegram_id(db, member.telegram_id)
    if existing_member:
        if existing_member.family_id:
            logger.warning(f"Member with telegram_id: {member.telegram_id} already belongs to family: {existing_member.family_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This member already belongs to a family"
            )
    
    created_member = FamilyService.add_member_to_family(db, family_id, member)
    logger.info(f"Member added successfully: {created_member.id} to family: {family_id}")
    return created_member

@router.get("/{family_id}/balances", response_model=List[MemberBalance])
def get_family_balances(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    debug: bool = Query(False, description="Show detailed debug information"),
    db: Session = Depends(get_db)
):
    """
    Get the financial balances of all members in a family.
    
    Args:
        family_id: ID of the family to get balances for
        telegram_id: Optional Telegram ID for permission validation
        debug: If True, enable detailed logging of balance calculations
        db: Database session
        
    Returns:
        List[MemberBalance]: List of financial balances for each family member
        
    Raises:
        HTTPException: If the family is not found or the user doesn't have permission to view the balances
    """
    logger.info(f"Request to get balances for family: {family_id}, requested by telegram_id: {telegram_id}, debug: {debug}")
    
    # Check if the family exists
    family = FamilyService.get_family(db, family_id)
    if not family:
        logger.warning(f"Family not found with ID: {family_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found"
        )
    
    # If a telegram_id is provided, verify that the user belongs to the family
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not member or member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to view balances for family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this family's balances"
            )
    
    # Calculate the balances with debug mode if requested
    balances = BalanceService.calculate_family_balances(db, family_id, debug_mode=debug)
    
    # Verificar la consistencia de los balances
    is_consistent = BalanceService.verify_balance_consistency(db, family_id)
    if not is_consistent:
        # Loguear el error pero no interrumpir la respuesta
        logger.warning(f"Inconsistent balances detected for family {family_id}")
    
    logger.info(f"Retrieved {len(balances)} balances for family: {family_id}")
    return balances 

@router.delete("/{family_id}", status_code=status.HTTP_200_OK)
def delete_family(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="Telegram ID of the user"),
    confirm: bool = Query(False, description="Confirm deletion"),
    db: Session = Depends(get_db)
):
    """
    Eliminar una familia y todos sus datos relacionados.
    
    ¡ADVERTENCIA! Esta operación es destructiva y elimina permanentemente:
    - Todos los pagos asociados a la familia
    - Todos los gastos asociados a la familia
    - Todos los miembros de la familia
    - La familia en sí
    
    Args:
        family_id: ID de la familia a eliminar
        telegram_id: ID de Telegram opcional para validación de permisos
        confirm: Debe establecerse como True para confirmar la eliminación
        db: Sesión de base de datos
        
    Returns:
        dict: Información sobre el resultado de la operación
        
    Raises:
        HTTPException: Si la familia no se encuentra, el usuario no tiene permisos,
                       o la operación no está confirmada
    """
    logger.info(f"Request to delete family: {family_id}, requested by telegram_id: {telegram_id}, confirm: {confirm}")
    
    # Verificar que la operación está confirmada
    if not confirm:
        logger.warning(f"Deletion not confirmed for family: {family_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta operación es destructiva. Confirme la eliminación estableciendo confirm=true"
        )
    
    # Verificar que la familia existe
    family = FamilyService.get_family(db, family_id)
    if not family:
        logger.warning(f"Family not found with ID: {family_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Familia no encontrada"
        )
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not member or member.family_id != family_id:
            logger.warning(f"Permission denied for telegram_id: {telegram_id} to delete family: {family_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta familia"
            )
    
    # Eliminar la familia y sus datos relacionados
    result = FamilyService.delete_family(db, family_id)
    
    if not result["success"]:
        logger.error(f"Error deleting family: {family_id}: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    logger.info(f"Family deleted successfully: {family_id}")
    return result 