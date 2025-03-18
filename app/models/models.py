"""
Database Models Module

This module defines the SQLAlchemy ORM models that represent the database tables
and their relationships. These models are used to interact with the database
and define the structure of the data.

Models:
- Family: Represents a group of people sharing expenses
- Member: Represents a person belonging to a family
- Expense: Represents a financial expense paid by a member and split among others
- Payment: Represents a money transfer between two members
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from .database import Base

def generate_uuid():
    """
    Generate a UUID string for use as a primary key.
    
    Returns:
        str: A new UUID in string format
    """
    return str(uuid.uuid4())

class PaymentStatus(enum.Enum):
    """
    Enum for payment status values.
    
    Attributes:
        PENDING: Payment has been created but not confirmed by the recipient
        CONFIRM: Payment has been confirmed by the recipient
        INACTIVE: Payment has been rejected or cancelled
    """
    PENDING = "PENDING"
    CONFIRM = "CONFIRM"
    INACTIVE = "INACTIVE"

class Language(enum.Enum):
    """
    Enum for language preference.
    
    Attributes:
        EN: English
        ES: Spanish
        FR: French
    """
    EN = "EN"
    ES = "ES"
    FR = "FR"

# Many-to-many association table between expenses and members
expense_member_association = Table(
    'expense_member_association',
    Base.metadata,
    Column('expense_id', String(36), ForeignKey('expenses.id')),
    Column('member_id', String(36), ForeignKey('members.id'))
)

class Family(Base):
    """
    Family model representing a group of people sharing expenses.
    
    Attributes:
        id (str): Unique identifier for the family (UUID)
        name (str): Name of the family
        created_at (datetime): When the family was created
        members (relationship): Members belonging to this family
        expenses (relationship): Expenses associated with this family
        payments (relationship): Payments made within this family
    """
    __tablename__ = "families"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    members = relationship("Member", back_populates="family")
    expenses = relationship("Expense", back_populates="family")
    payments = relationship("Payment", back_populates="family")

class Member(Base):
    """
    Member model representing a person belonging to a family.
    
    Attributes:
        id (str): Unique identifier for the member (UUID)
        name (str): Name of the member
        telegram_id (str): Telegram ID used for authentication
        family_id (str): ID of the family this member belongs to
        language (Language): Preferred language for notifications and interface
        created_at (datetime): When the member was created
        family (relationship): The family this member belongs to
        expenses_paid (relationship): Expenses paid by this member
        payments_made (relationship): Payments sent by this member
        payments_received (relationship): Payments received by this member
        expenses_split (relationship): Expenses this member is part of
    """
    __tablename__ = "members"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String, index=True)
    telegram_id = Column(String, unique=True, index=True)
    family_id = Column(String(36), ForeignKey("families.id"))
    language = Column(Enum(Language), default=Language.EN, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    family = relationship("Family", back_populates="members")
    expenses_paid = relationship("Expense", back_populates="paid_by_member")
    payments_made = relationship("Payment", foreign_keys="Payment.from_member_id", back_populates="from_member")
    payments_received = relationship("Payment", foreign_keys="Payment.to_member_id", back_populates="to_member")
    expenses_split = relationship("Expense", secondary=expense_member_association, back_populates="split_among")

class Expense(Base):
    """
    Expense model representing a financial expense.
    
    Attributes:
        id (str): Unique identifier for the expense (UUID)
        description (str): Description of what the expense was for
        amount (float): The monetary amount of the expense
        paid_by (str): ID of the member who paid for the expense
        family_id (str): ID of the family this expense belongs to
        created_at (datetime): When the expense was created
        paid_by_member (relationship): The member who paid for the expense
        family (relationship): The family this expense belongs to
        split_among (relationship): Members who share this expense
    """
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    description = Column(String, index=True)
    amount = Column(Float)
    paid_by = Column(String(36), ForeignKey("members.id"))
    family_id = Column(String(36), ForeignKey("families.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    paid_by_member = relationship("Member", back_populates="expenses_paid")
    family = relationship("Family", back_populates="expenses")
    split_among = relationship("Member", secondary=expense_member_association, back_populates="expenses_split")

class Payment(Base):
    """
    Payment model representing a money transfer between two members.
    
    Attributes:
        id (str): Unique identifier for the payment (UUID)
        from_member_id (str): ID of the member sending the payment
        to_member_id (str): ID of the member receiving the payment
        amount (float): The monetary amount of the payment
        status (PaymentStatus): Current status of the payment
        family_id (str): ID of the family this payment belongs to
        created_at (datetime): When the payment was created
        from_member (relationship): The member sending the payment
        to_member (relationship): The member receiving the payment
        family (relationship): The family this payment belongs to
    """
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    from_member_id = Column(String(36), ForeignKey("members.id"))
    to_member_id = Column(String(36), ForeignKey("members.id"))
    amount = Column(Float)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.CONFIRM, nullable=False)
    family_id = Column(String(36), ForeignKey("families.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    from_member = relationship("Member", foreign_keys=[from_member_id], back_populates="payments_made")
    to_member = relationship("Member", foreign_keys=[to_member_id], back_populates="payments_received")
    family = relationship("Family", back_populates="payments") 