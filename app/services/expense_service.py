from sqlalchemy.orm import Session
from app.models.models import Expense, Member
from app.models.schemas import ExpenseCreate, ExpenseUpdate

class ExpenseService:
    """Servicio para manejar los gastos."""
    
    @staticmethod
    def create_expense(db: Session, expense: ExpenseCreate):
        """Crea un nuevo gasto."""
        # Crear el gasto sin el campo split_among primero
        db_expense = Expense(
            description=expense.description,
            amount=expense.amount,
            paid_by=expense.paid_by
        )
        
        # Obtener la familia del miembro que paga
        payer = db.query(Member).filter(Member.id == expense.paid_by).first()
        if payer:
            db_expense.family_id = payer.family_id
            
            # Si no se especifica split_among, dividir entre todos los miembros de la familia
            if not expense.split_among:
                # Obtener todos los miembros de la familia
                family_members = db.query(Member).filter(Member.family_id == payer.family_id).all()
                db_expense.split_among = family_members
            else:
                # Usar los miembros especificados
                members = db.query(Member).filter(Member.id.in_(expense.split_among)).all()
                db_expense.split_among = members
        
        db.add(db_expense)
        db.commit()
        db.refresh(db_expense)
        return db_expense
    
    @staticmethod
    def get_expense(db: Session, expense_id: str):
        """Obtiene un gasto por su ID."""
        return db.query(Expense).filter(Expense.id == expense_id).first()
    
    @staticmethod
    def get_expenses_by_member(db: Session, member_id: int):
        """Obtiene los gastos pagados por un miembro."""
        return db.query(Expense).filter(Expense.paid_by == member_id).all()
    
    @staticmethod
    def get_expenses_by_family(db: Session, family_id: str):
        """Obtiene los gastos de una familia."""
        # Obtener los IDs de los miembros de la familia
        member_ids = [m.id for m in db.query(Member).filter(Member.family_id == family_id).all()]
        
        # Obtener los gastos donde el pagador es un miembro de la familia
        return db.query(Expense).filter(Expense.paid_by.in_(member_ids)).all()
    
    @staticmethod
    def update_expense(db: Session, expense_id: str, expense_update: ExpenseUpdate):
        """Actualiza un gasto existente."""
        db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not db_expense:
            return None
        
        # Actualizar los campos proporcionados
        if expense_update.description is not None:
            db_expense.description = expense_update.description
        
        if expense_update.amount is not None:
            db_expense.amount = expense_update.amount
        
        if expense_update.paid_by is not None:
            db_expense.paid_by = expense_update.paid_by
            
            # Actualizar la familia si cambia el pagador
            payer = db.query(Member).filter(Member.id == expense_update.paid_by).first()
            if payer:
                db_expense.family_id = payer.family_id
        
        # Actualizar split_among si se proporciona
        if expense_update.split_among is not None:
            if not expense_update.split_among:
                # Si la lista está vacía, dividir entre todos los miembros de la familia
                family_members = db.query(Member).filter(Member.family_id == db_expense.family_id).all()
                db_expense.split_among = family_members
            else:
                # Usar los miembros especificados
                members = db.query(Member).filter(Member.id.in_(expense_update.split_among)).all()
                db_expense.split_among = members
        
        db.commit()
        db.refresh(db_expense)
        return db_expense
    
    @staticmethod
    def delete_expense(db: Session, expense_id: str):
        """Elimina un gasto."""
        db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if db_expense:
            db.delete(db_expense)
            db.commit()
        return db_expense 