from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GroupCreate(BaseModel):
    name: str
    user: str

# when user will ask for a group , it will give 
# The group ID
# The group name
# The user who created it (created_by)"
class GroupOut(BaseModel):
    id: int
    name: str
    created_by: int

    class Config:
        from_attributes = True

class ExpensePayer(BaseModel):
    user_id: int
    amount: float

class ExpenseShare(BaseModel):
    user_id: int
    amount: float

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    group_id: int
    paid_by: List[ExpensePayer]
    split_between: List[ExpenseShare]
    type: str  # equal, percentage, manual
    user:int

class ExpenseOut(BaseModel):
    id: int
    description: str
    amount: float
    created_by: int
    group_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BalanceWithUser(BaseModel):
    user_id: int
    balance: float

class BalanceSummary(BaseModel):
    total_outstanding: float
    per_user_balance: List[BalanceWithUser]

class SettleCreate(BaseModel):
    from_user: int
    to_user: int
    amount: float
