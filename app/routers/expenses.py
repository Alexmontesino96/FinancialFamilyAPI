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
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Crea un nuevo gasto."""
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la misma familia que el pagador
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer or requesting_member.family_id != payer.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para crear gastos para este miembro"
            )
    
    return ExpenseService.create_expense(db, expense)

@router.get("/{expense_id}", response_model=Expense)
def get_expense(
    expense_id: str,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene un gasto por su ID."""
    expense = ExpenseService.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la misma familia que el pagador
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer or requesting_member.family_id != payer.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este gasto"
            )
    
    return expense

@router.put("/{expense_id}", response_model=Expense)
def update_expense(
    expense_id: str,
    expense_update: ExpenseUpdate,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Actualiza un gasto existente."""
    # Verificar que el gasto existe
    expense = ExpenseService.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la misma familia que el pagador
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer or requesting_member.family_id != payer.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para actualizar este gasto"
            )
    
    # Si se cambia el pagador, verificar que el nuevo pagador pertenece a la misma familia
    if expense_update.paid_by is not None and expense_update.paid_by != expense.paid_by:
        new_payer = MemberService.get_member(db, expense_update.paid_by)
        if not new_payer or new_payer.family_id != expense.family_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nuevo pagador debe pertenecer a la misma familia"
            )
    
    # Actualizar el gasto
    updated_expense = ExpenseService.update_expense(db, expense_id, expense_update)
    if not updated_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error al actualizar el gasto"
        )
    
    return updated_expense

@router.get("/member/{member_id}", response_model=List[Expense])
def get_member_expenses(
    member_id: int,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Obtiene los gastos de un miembro."""
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
                detail="No tienes permiso para ver los gastos de este miembro"
            )
    
    return ExpenseService.get_expenses_by_member(db, member_id)

@router.get("/family/{family_id}", response_model=List[Expense])
def get_family_expenses(
    family_id: str,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    print(f"family_id: {family_id}")
    """Obtiene los gastos de una familia."""
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la familia
    if telegram_id:
        member = MemberService.get_member_by_telegram_id(db, telegram_id)
        
        if not member or member.family_id != family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver los gastos de esta familia"
            )
    
    return ExpenseService.get_expenses_by_family(db, family_id)

@router.delete("/{expense_id}", response_model=Expense)
def delete_expense(
    expense_id: str,
    telegram_id: Optional[str] = Query(None, description="ID de Telegram del usuario"),
    db: Session = Depends(get_db)
):
    """Elimina un gasto."""
    expense = ExpenseService.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado"
        )
    
    # Si se proporciona un telegram_id, verificar que el usuario pertenece a la misma familia que el pagador
    if telegram_id:
        requesting_member = MemberService.get_member_by_telegram_id(db, telegram_id)
        payer = MemberService.get_member(db, expense.paid_by)
        
        if not requesting_member or not payer or requesting_member.family_id != payer.family_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar este gasto"
            )
    
    return ExpenseService.delete_expense(db, expense_id) 