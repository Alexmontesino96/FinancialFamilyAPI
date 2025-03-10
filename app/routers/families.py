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
    """Crea una nueva familia."""
    return FamilyService.create_family(db, family)

@router.get("/{family_id}", response_model=Family)
def get_family(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene información de una familia."""
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a esta familia"
            )
    
    family = FamilyService.get_family(db, family_id)
    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Familia no encontrada"
        )
    return family

@router.get("/{family_id}/members", response_model=List[Member])
def get_family_members(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene los miembros de una familia."""
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a esta familia"
            )
    
    return FamilyService.get_family_members(db, family_id)

@router.post("/{family_id}/members", response_model=Member, status_code=status.HTTP_201_CREATED)
def add_member_to_family(
    family_id: str,
    member: MemberCreate,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Añade un miembro a una familia."""
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        existing_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not existing_member or existing_member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a esta familia"
            )
    
    # Verificar si el miembro ya existe
    existing_member = MemberService.get_member_by_telegram_id(db, member.telegram_id)
    if existing_member:
        if existing_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este miembro ya pertenece a una familia"
            )
    
    return FamilyService.add_member_to_family(db, family_id, member)

@router.get("/{family_id}/balances")
def get_family_balances(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene los balances de una familia."""
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a esta familia"
            )
    
    return BalanceService.calculate_family_balances(db, family_id) 