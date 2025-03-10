from sqlalchemy.orm import Session
from app.models.models import Member
from app.models.schemas import MemberCreate, MemberUpdate

class MemberService:
    """Servicio para manejar los miembros."""
    
    @staticmethod
    def create_member(db: Session, member: MemberCreate):
        """Crea un nuevo miembro."""
        db_member = Member(
            name=member.name,
            telegram_id=member.telegram_id,
            family_id=member.family_id
        )
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        return db_member
    
    @staticmethod
    def get_member(db: Session, member_id: int):
        """Obtiene un miembro por su ID."""
        return db.query(Member).filter(Member.id == member_id).first()
    
    @staticmethod
    def get_member_by_telegram_id(db: Session, telegram_id: str):
        """Obtiene un miembro por su ID de Telegram."""
        return db.query(Member).filter(Member.telegram_id == telegram_id).first()
    
    @staticmethod
    def update_member(db: Session, member_id: int, member: MemberUpdate):
        """Actualiza un miembro."""
        db_member = MemberService.get_member(db, member_id)
        if not db_member:
            return None
        
        # Actualizar los campos
        for key, value in member.dict(exclude_unset=True).items():
            setattr(db_member, key, value)
        
        db.commit()
        db.refresh(db_member)
        return db_member
    
    @staticmethod
    def delete_member(db: Session, member_id: int):
        """Elimina un miembro."""
        db_member = MemberService.get_member(db, member_id)
        if not db_member:
            return None
        
        db.delete(db_member)
        db.commit()
        return db_member 