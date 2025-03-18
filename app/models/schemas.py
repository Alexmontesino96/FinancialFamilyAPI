"""
Pydantic Schemas Module

This module defines the Pydantic models used for data validation, serialization,
and documentation. These schemas define the structure of request and response data
for the API endpoints.

The schemas are organized by resource type (auth, members, families, expenses, payments)
and include base models, creation models, update models, and response models.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import enum
from app.models.models import Language as DBLanguage

# Authentication schemas
class Token(BaseModel):
    """
    Token schema for authentication responses.
    
    Attributes:
        access_token (str): JWT access token
        token_type (str): Type of token (e.g., "bearer")
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Token data schema for decoded JWT payload.
    
    Attributes:
        username (Optional[str]): Username extracted from the token
    """
    username: Optional[str] = None

# Language enum for Pydantic models
class Language(str, enum.Enum):
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

# Member schemas
class MemberBase(BaseModel):
    """
    Base schema for member data.
    
    Attributes:
        name (str): Name of the member
        telegram_id (str): Telegram ID used for authentication
        language (Language): Preferred language for notifications and interface
    """
    name: str
    telegram_id: str
    language: Language = Language.EN

class MemberCreate(MemberBase):
    """
    Schema for creating a new member.
    Inherits all fields from MemberBase.
    """
    pass

class MemberUpdate(BaseModel):
    """
    Schema for updating an existing member.
    All fields are optional to allow partial updates.
    
    Attributes:
        name (Optional[str]): New name for the member
        telegram_id (Optional[str]): New Telegram ID for the member
        language (Optional[Language]): New preferred language for the member
    """
    name: Optional[str] = None
    telegram_id: Optional[str] = None
    language: Optional[Language] = None

class Member(MemberBase):
    """
    Schema for member responses.
    
    Attributes:
        id (str): Unique identifier for the member
        family_id (str): ID of the family this member belongs to
        created_at (datetime): When the member was created
    """
    id: str
    family_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Family schemas
class FamilyBase(BaseModel):
    """
    Base schema for family data.
    
    Attributes:
        name (str): Name of the family
    """
    name: str

class FamilyCreate(FamilyBase):
    """
    Schema for creating a new family.
    
    Attributes:
        members (List[MemberCreate]): Initial members of the family
    """
    members: List[MemberCreate]

class Family(FamilyBase):
    """
    Schema for family responses.
    
    Attributes:
        id (str): Unique identifier for the family
        created_at (datetime): When the family was created
        members (List[Member]): Members belonging to this family
    """
    id: str
    created_at: datetime
    members: List[Member] = []

    class Config:
        from_attributes = True

# Expense schemas
class ExpenseBase(BaseModel):
    """
    Base schema for expense data.
    
    Attributes:
        description (str): Description of what the expense was for
        amount (float): The monetary amount of the expense
        paid_by (str): ID of the member who paid for the expense
    """
    description: str
    amount: float
    paid_by: str

class ExpenseCreate(ExpenseBase):
    """
    Schema for creating a new expense.
    
    Attributes:
        split_among (Optional[List[str]]): IDs of members who share this expense
    """
    split_among: Optional[List[str]] = None

class ExpenseUpdate(BaseModel):
    """
    Schema for updating an existing expense.
    All fields are optional to allow partial updates.
    
    Attributes:
        description (Optional[str]): New description for the expense
        amount (Optional[float]): New amount for the expense
        paid_by (Optional[str]): New member ID who paid for the expense
        split_among (Optional[List[str]]): New list of member IDs who share this expense
    """
    description: Optional[str] = None
    amount: Optional[float] = None
    paid_by: Optional[str] = None
    split_among: Optional[List[str]] = None

class Expense(ExpenseBase):
    """
    Schema for expense responses.
    
    Attributes:
        id (str): Unique identifier for the expense
        family_id (str): ID of the family this expense belongs to
        created_at (datetime): When the expense was created
        split_among (List[Member]): Members who share this expense
    """
    id: str
    family_id: str
    created_at: datetime
    split_among: List[Member] = []

    class Config:
        from_attributes = True

# Payment schemas
class PaymentStatus(str, enum.Enum):
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

class PaymentBase(BaseModel):
    """
    Base schema for payment data.
    
    Attributes:
        from_member (str): ID of the member sending the payment
        to_member (str): ID of the member receiving the payment
        amount (float): The monetary amount of the payment
    """
    from_member: str
    to_member: str
    amount: float

class PaymentCreate(PaymentBase):
    """
    Schema for creating a new payment.
    Inherits all fields from PaymentBase.
    
    Note:
        The status field is not included as it is automatically set to CONFIRM upon creation.
        New payments are automatically confirmed to affect balances immediately.
    """
    pass

class PaymentUpdate(BaseModel):
    """
    Schema for updating a payment's status.
    
    Attributes:
        status (PaymentStatus): New status for the payment
    """
    status: PaymentStatus

class Payment(BaseModel):
    """
    Schema for payment responses.
    
    Attributes:
        id (str): Unique identifier for the payment
        from_member (Member): Member sending the payment 
        to_member (Member): Member receiving the payment
        amount (float): The monetary amount of the payment
        status (PaymentStatus): Current status of the payment
        family_id (str): ID of the family this payment belongs to
        created_at (datetime): When the payment was created
    """
    id: str
    from_member: Member
    to_member: Member
    amount: float
    status: PaymentStatus
    family_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Balance schemas
class DebtDetail(BaseModel):
    """
    Schema for debt details in balance calculations.
    
    Attributes:
        to_id (str): ID of the member who is owed money
        to_name (str): Name of the member who is owed money (for display purposes)
        amount (float): Amount of money owed
    """
    to_id: str
    to_name: str = Field(..., alias="to")
    amount: float
    
    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "to_id": "abc123",
                "to": "Juan Pérez", 
                "amount": 100.0
            }
        }
    }

class CreditDetail(BaseModel):
    """
    Schema for credit details in balance calculations.
    
    Attributes:
        from_id (str): ID of the member who owes money
        from_name (str): Name of the member who owes money (for display purposes)
        amount (float): Amount of money owed
    """
    from_id: str
    from_name: str = Field(..., alias="from")
    amount: float

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "from_id": "abc123",
                "from": "María García",
                "amount": 50.0
            }
        }
    }

class MemberBalance(BaseModel):
    """
    Schema for member balance calculations.
    
    Attributes:
        member_id (str): ID of the member
        name (str): Name of the member
        total_debt (float): Total amount this member owes to others
        total_owed (float): Total amount others owe to this member
        net_balance (float): Net balance (positive means others owe this member)
        debts (List[DebtDetail]): Detailed breakdown of debts to other members
        credits (List[CreditDetail]): Detailed breakdown of credits from other members
    """
    member_id: str
    name: str
    total_debt: float
    total_owed: float
    net_balance: float
    debts: List[DebtDetail] = []
    credits: List[CreditDetail] = []

    model_config = {
        "populate_by_name": True
    } 