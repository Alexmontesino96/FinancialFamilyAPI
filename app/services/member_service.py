from sqlalchemy.orm import Session
from app.models.models import Member
from app.models.schemas import MemberCreate, MemberUpdate

class MemberService:
    """
    Service for managing members.
    
    This class provides methods for creating, retrieving, updating, and deleting
    members in the database.
    """
    
    @staticmethod
    def create_member(db: Session, member: MemberCreate):
        """
        Create a new member.
        
        Args:
            db: Database session
            member: Member data to create
            
        Returns:
            Member: The created member
        """
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
        """
        Get a member by their ID.
        
        Args:
            db: Database session
            member_id: ID of the member to retrieve
            
        Returns:
            Member: The requested member or None if not found
        """
        return db.query(Member).filter(Member.id == member_id).first()
    
    @staticmethod
    def get_member_by_telegram_id(db: Session, telegram_id: str):
        """
        Get a member by their Telegram ID.
        
        Args:
            db: Database session
            telegram_id: Telegram ID of the member to retrieve
            
        Returns:
            Member: The requested member or None if not found
        """
        return db.query(Member).filter(Member.telegram_id == telegram_id).first()
    
    @staticmethod
    def update_member(db: Session, member_id: int, member: MemberUpdate):
        """
        Update a member's information.
        
        Args:
            db: Database session
            member_id: ID of the member to update
            member: Updated member data
            
        Returns:
            Member: The updated member or None if not found
        """
        db_member = MemberService.get_member(db, member_id)
        if not db_member:
            return None
        
        # Update the fields
        for key, value in member.dict(exclude_unset=True).items():
            setattr(db_member, key, value)
        
        db.commit()
        db.refresh(db_member)
        return db_member
    
    @staticmethod
    def delete_member(db: Session, member_id: int):
        """
        Delete a member.
        
        Args:
            db: Database session
            member_id: ID of the member to delete
            
        Returns:
            Member: The deleted member or None if not found
        """
        db_member = MemberService.get_member(db, member_id)
        if not db_member:
            return None
        
        db.delete(db_member)
        db.commit()
        return db_member 