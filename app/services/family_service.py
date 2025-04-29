from sqlalchemy.orm import Session
from app.models.models import Family, Member, Payment, Expense
from app.models.schemas import FamilyCreate, MemberCreate
from app.utils.logging_config import get_logger

# Configurar logging centralizado
logger = get_logger("family_service")

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
        logger.info(f"Creating new family with name: {family.name}")
        logger.info(f"Initial member count: {len(family.members)}")
        
        # Create the family
        db_family = Family(name=family.name)
        db.add(db_family)
        db.commit()
        db.refresh(db_family)
        
        logger.info(f"Family created with ID: {db_family.id}")
        
        # Create the members
        for member_data in family.members:
            logger.debug(f"Adding member: {member_data.name} to family {db_family.id}")
            db_member = Member(
                name=member_data.name,
                telegram_id=member_data.telegram_id,
                family_id=db_family.id
            )
            db.add(db_member)
        
        db.commit()
        db.refresh(db_family)
        logger.info(f"Created family '{family.name}' with {len(db_family.members)} members")
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
        logger.debug(f"Getting family with ID: {family_id}")
        family = db.query(Family).filter(Family.id == family_id).first()
        if family:
            logger.debug(f"Found family: {family.name} (ID: {family.id})")
        else:
            logger.debug(f"Family not found with ID: {family_id}")
        return family
    
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
        logger.debug(f"Getting members for family: {family_id}")
        members = db.query(Member).filter(Member.family_id == family_id).all()
        logger.debug(f"Found {len(members)} members for family {family_id}")
        return members
    
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
        logger.info(f"Adding member {member.name} to family {family_id}")
        
        # Check if the member already exists
        existing_member = db.query(Member).filter(Member.telegram_id == member.telegram_id).first()
        if existing_member:
            logger.info(f"Member already exists with Telegram ID {member.telegram_id}: {existing_member.name} (ID: {existing_member.id})")
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
        logger.info(f"Member {member.name} added to family {family_id} with ID: {db_member.id}")
        return db_member
        
    @staticmethod
    def delete_family(db: Session, family_id: str):
        """
        Elimina una familia y todos sus datos relacionados.
        
        Esta operación es destructiva y elimina:
        1. Todos los pagos asociados a la familia
        2. Todos los gastos asociados a la familia
        3. Todos los miembros de la familia
        4. La familia en sí
        
        Args:
            db: Sesión de base de datos
            family_id: ID de la familia a eliminar
            
        Returns:
            dict: Un diccionario con información sobre el resultado de la operación
            
        Note:
            Esta operación no se puede deshacer y borra todos los datos relacionados con la familia.
        """
        from app.models.models import Payment, Expense
        
        logger.info(f"Requested deletion of family with ID: {family_id}")
        
        # Verificar que la familia existe
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            logger.warning(f"Attempted to delete non-existent family: {family_id}")
            return {"success": False, "message": "Familia no encontrada"}
        
        # Contar registros antes de eliminar para informar
        members_count = db.query(Member).filter(Member.family_id == family_id).count()
        expenses_count = db.query(Expense).filter(Expense.family_id == family_id).count()
        payments_count = db.query(Payment).filter(Payment.family_id == family_id).count()
        
        logger.info(f"Deleting family '{family.name}' (ID: {family_id}) with {members_count} members, {expenses_count} expenses, and {payments_count} payments")
        
        try:
            # Eliminar pagos asociados a la familia
            logger.debug(f"Deleting {payments_count} payments for family {family_id}")
            db.query(Payment).filter(Payment.family_id == family_id).delete()
            
            # Eliminar gastos asociados a la familia
            logger.debug(f"Deleting {expenses_count} expenses for family {family_id}")
            db.query(Expense).filter(Expense.family_id == family_id).delete()
            
            # Eliminar miembros de la familia
            logger.debug(f"Deleting {members_count} members for family {family_id}")
            db.query(Member).filter(Member.family_id == family_id).delete()
            
            # Eliminar la familia
            logger.debug(f"Deleting family record: {family_id}")
            db.delete(family)
            
            db.commit()
            logger.info(f"Family {family_id} and all related data successfully deleted")
            
            return {
                "success": True,
                "message": "Familia eliminada correctamente",
                "deleted": {
                    "family": family.name,
                    "members": members_count,
                    "expenses": expenses_count,
                    "payments": payments_count
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting family {family_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Error al eliminar la familia: {str(e)}"
            } 