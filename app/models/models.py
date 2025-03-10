from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base

# Función para generar UUIDs por defecto
def generate_uuid():
    return str(uuid.uuid4())

# Tabla de asociación para la relación muchos a muchos entre gastos y miembros
expense_member_association = Table(
    'expense_member_association',
    Base.metadata,
    Column('expense_id', String(36), ForeignKey('expenses.id')),
    Column('member_id', Integer, ForeignKey('members.id'))
)

class Family(Base):
    """Modelo para las familias."""
    __tablename__ = "families"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    members = relationship("Member", back_populates="family")
    expenses = relationship("Expense", back_populates="family")
    payments = relationship("Payment", back_populates="family")

class Member(Base):
    """Modelo para los miembros de una familia."""
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    telegram_id = Column(String, unique=True, index=True)
    family_id = Column(String(36), ForeignKey("families.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    family = relationship("Family", back_populates="members")
    expenses_paid = relationship("Expense", back_populates="paid_by_member")
    payments_made = relationship("Payment", foreign_keys="Payment.from_member_id", back_populates="from_member")
    payments_received = relationship("Payment", foreign_keys="Payment.to_member_id", back_populates="to_member")
    expenses_split = relationship("Expense", secondary=expense_member_association, back_populates="split_among")

class Expense(Base):
    """Modelo para los gastos."""
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    description = Column(String, index=True)
    amount = Column(Float)
    paid_by = Column(Integer, ForeignKey("members.id"))
    family_id = Column(String(36), ForeignKey("families.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    paid_by_member = relationship("Member", back_populates="expenses_paid")
    family = relationship("Family", back_populates="expenses")
    split_among = relationship("Member", secondary=expense_member_association, back_populates="expenses_split")

class Payment(Base):
    """Modelo para los pagos entre miembros."""
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    from_member_id = Column(Integer, ForeignKey("members.id"))
    to_member_id = Column(Integer, ForeignKey("members.id"))
    amount = Column(Float)
    family_id = Column(String(36), ForeignKey("families.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    from_member = relationship("Member", foreign_keys=[from_member_id], back_populates="payments_made")
    to_member = relationship("Member", foreign_keys=[to_member_id], back_populates="payments_received")
    family = relationship("Family", back_populates="payments") 