from sqlalchemy.orm import Session
from app.models.models import Family, Member
from app.models.schemas import FamilyCreate, MemberCreate

class FamilyService:
    """
    Service for managing families.
    
    This class provides methods for creating, retrieving, and managing families
    and their members in the database.
    """
    
    @staticmethod
    def create_family(db: Session, family: FamilyCreate):
        """
        Create a new family with its initial members.
        
        Args:
            db: Database session
            family: Family data including initial members
            
        Returns:
            Family: The created family with its members
        """
        # Create the family
        db_family = Family(name=family.name)
        db.add(db_family)
        db.commit()
        db.refresh(db_family)
        
        # Create the members
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
        """
        Get a family by its ID.
        
        Args:
            db: Database session
            family_id: ID of the family to retrieve
            
        Returns:
            Family: The requested family or None if not found
        """
        return db.query(Family).filter(Family.id == family_id).first()
    
    @staticmethod
    def get_family_members(db: Session, family_id: str):
        """
        Get all members of a family.
        
        Args:
            db: Database session
            family_id: ID of the family to get members for
            
        Returns:
            List[Member]: List of family members
        """
        return db.query(Member).filter(Member.family_id == family_id).all()
    
    @staticmethod
    def add_member_to_family(db: Session, family_id: str, member: MemberCreate):
        """
        Add a member to a family.
        
        Args:
            db: Database session
            family_id: ID of the family to add the member to
            member: Member data to create
            
        Returns:
            Member: The created or existing member
            
        Note:
            If a member with the same Telegram ID already exists, that member is returned
            instead of creating a new one.
        """
        # Check if the member already exists
        existing_member = db.query(Member).filter(Member.telegram_id == member.telegram_id).first()
        if existing_member:
            return existing_member
        
        # Create the new member
        db_member = Member(
            name=member.name,
            telegram_id=member.telegram_id,
            family_id=family_id
        )
        db.add(db_member)
        db.commit()
        db.refresh(db_member)
        return db_member 