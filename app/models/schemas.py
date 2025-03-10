from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Esquemas para autenticación
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Esquemas para miembros
class MemberBase(BaseModel):
    name: str
    telegram_id: str

class MemberCreate(MemberBase):
    pass

class MemberUpdate(BaseModel):
    name: Optional[str] = None
    telegram_id: Optional[str] = None

class Member(MemberBase):
    id: int
    family_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Esquemas para familias
class FamilyBase(BaseModel):
    name: str

class FamilyCreate(FamilyBase):
    members: List[MemberCreate]

class Family(FamilyBase):
    id: str
    created_at: datetime
    members: List[Member] = []

    class Config:
        from_attributes = True

# Esquemas para gastos
class ExpenseBase(BaseModel):
    description: str
    amount: float
    paid_by: int

class ExpenseCreate(ExpenseBase):
    split_among: Optional[List[int]] = None

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    paid_by: Optional[int] = None
    split_among: Optional[List[int]] = None

class Expense(ExpenseBase):
    id: str
    family_id: str
    created_at: datetime
    split_among: List[Member] = []

    class Config:
        from_attributes = True

# Esquemas para pagos
class PaymentBase(BaseModel):
    from_member: int
    to_member: int
    amount: float

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: str
    family_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# Esquemas para balances
class DebtDetail(BaseModel):
    to: str
    amount: float

class CreditDetail(BaseModel):
    from_: str = Field(..., alias="from")
    amount: float

class MemberBalance(BaseModel):
    member_id: str
    name: str
    total_debt: float
    total_owed: float
    net_balance: float
    debts: List[DebtDetail] = []
    credits: List[CreditDetail] = []

    class Config:
        populate_by_name = True 