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
    """Obtiene un miembro por su ID de Telegram."""
    member = MemberService.get_member_by_telegram_id(db, telegram_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    return member

@router.get("/id/{member_id}", response_model=Member)
def get_member_by_id(
    member_id: int,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene un miembro por su ID."""
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
                detail="No tienes permiso para acceder a este miembro"
            )
    
    return member

@router.get("/me/balance", response_model=MemberBalance)
def get_current_member_balance(
    telegram_id: str = Query(..., description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene el balance del miembro actual."""
    member = MemberService.get_member_by_telegram_id(db, telegram_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    if not member.family_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El miembro no pertenece a ninguna familia"
        )
    
    return BalanceService.get_member_balance(db, member.family_id, member.id)

@router.put("/{member_id}", response_model=Member)
def update_member(
    member_id: int,
    member: MemberUpdate,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Actualiza un miembro."""
    db_member = MemberService.get_member(db, member_id)
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar que el usuario es el mismo o pertenece a la misma familia
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not requesting_member or (requesting_member.id != member_id and requesting_member.family_id != db_member.family_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar este miembro"
            )
    
    return MemberService.update_member(db, member_id, member)

@router.delete("/{member_id}", response_model=Member)
def delete_member(
    member_id: int,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Elimina un miembro."""
    # Verificar que el miembro a eliminar existe
    db_member = MemberService.get_member(db, member_id)
    if not db_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Miembro no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la misma familia
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        if not requesting_member or requesting_member.family_id != db_member.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar este miembro"
            )
    
    return MemberService.delete_member(db, member_id) 