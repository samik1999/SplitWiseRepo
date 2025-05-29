# app/schemas.py
# Pydantic models. 

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, TypeVar, Generic
from datetime import datetime
from decimal import Decimal

# --- Standard API Response Structures ---
DataType = TypeVar('DataType')
class StandardApiResponse(BaseModel, Generic[DataType]):
    success: bool = True; message: Optional[str] = None; data: Optional[DataType] = None
class ApiErrorDetail(BaseModel):
    field: Optional[str] = None; error_message: str
class ErrorApiResponse(BaseModel):
    success: bool = False; message: str = "An error occurred."; errors: Optional[List[ApiErrorDetail]] = None

# --- User Schemas ---
class UserCreateSchema(BaseModel): 
    name: str = Field(..., examples=["alice_unique"])
    email: EmailStr; password: str = Field(..., min_length=1)
class UserLoginSchema(BaseModel): email: EmailStr; password: str
class UserPublicInfoSchema(BaseModel):
    id: int; name: str; email: EmailStr
    class Config: from_attributes = True

# --- Group Schemas ---
class GroupCreateSchema(BaseModel): 
    name: str = Field(..., examples=["Weekend Trip"])
class GroupPublicInfoSchema(BaseModel):
    id: int; name: str; created_by_id: int
    class Config: from_attributes = True

# --- Schemas for Name-Based Inputs ---
class UserNameSchema(BaseModel): 
    name: str

class ExpensePayerByNameSchema(BaseModel):
    user_name: str = Field(..., description="NAME of the user who paid")
    amount: Decimal = Field(..., gt=Decimal('0'))

class ExpenseShareByNameSchema(BaseModel):
    user_name: str = Field(..., description="NAME of the user this share is for")
    amount: Decimal = Field(..., gt=Decimal('0'), description="Share amount or percentage")

class ExpenseCreateUsingNamesSchema(BaseModel):
    description: str; amount: Decimal = Field(..., gt=Decimal('0'))
    group_name: str = Field(..., description="NAME of the group for this expense")
    # creator_user_name will be a query parameter in the router
    paid_by: List[ExpensePayerByNameSchema] = Field(..., min_length=1)
    split_between: List[ExpenseShareByNameSchema] = Field(..., min_length=1)
    split_type: str = Field(..., examples=["equal", "manual", "percentage"])

class ExpensePublicInfoSchema(BaseModel): # Output schema
    id: int; description: str; amount: Decimal; group_id: int
    created_by_id: int; created_at: datetime
    class Config: from_attributes = True

# --- Balance and Settlement Schemas ---
class BalanceDetailSchema(BaseModel):
    other_user_id: int 
    other_user_name: Optional[str] = None 
    balance_amount: Decimal

class UserOverallBalanceSchema(BaseModel):
    net_total_balance: Decimal
    balance_with_each_user: List[BalanceDetailSchema]

class SettlementCreateUsingNamesSchema(BaseModel): 
    from_user_name: str = Field(..., description="NAME of user making payment")
    to_user_name: str = Field(..., description="NAME of user receiving payment")
    amount: Decimal = Field(..., gt=Decimal('0'))

class SettlementPublicInfoSchema(BaseModel): 
    id: int; from_user_id: int; to_user_id: int; amount: Decimal; settled_at: datetime
    class Config: from_attributes = True