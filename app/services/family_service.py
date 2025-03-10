from sqlalchemy.orm import Session
from app.models.models import Family, Member
from app.models.schemas import FamilyCreate, MemberCreate

class FamilyService:
    """Servicio para manejar las familias."""
    
    @staticmethod
    def create_family(db: Session, family: FamilyCreate):
        """Crea una nueva familia con sus miembros iniciales."""
        # Crear la familia
        db_family = Family(name=family.name)
        db.add(db_family)
        db.commit()
        db.refresh(db_family)
        
        # Crear los miembros
        for member_data in family.members:
            db_member = Member(
                name=member_data.name,
                telegram_id=member_data.telegram_id,
                family_id=db_family.id
            )
            db.add(db_member)
        
        db.commit()
        db.refresh(db_family)
        return db_family
    
    @staticmethod
    def get_family(db: Session, family_id: str):
        """Obtiene una familia por su ID."""
        return db.query(Family).filter(Family.id == family_id).first()
    
    @staticmethod
    def get_family_members(db: Session, family_id: str):
        """Obtiene los miembros de una familia."""
        return db.query(Member).filter(Member.family_id == family_id).all()
    
    @staticmethod
    def add_member_to_family(db: Session, family_id: str, member: MemberCreate):
        """Añade un miembro a una familia."""
        # Verificar si el miembro ya existe
        existing_member = db.query(Member).filter(Member.telegram_id == member.telegram_id).first()
        if existing_member:
            return existing_member
        
        # Crear el nuevo miembro
        db_member = Member(
            name=member.name,
            telegram_id=member.telegram_id,
            family_id=family_id
        )
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        return db_member 