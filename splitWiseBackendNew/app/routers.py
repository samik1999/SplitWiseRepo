# app/routers.py
# API routes. Uses names instead of IDs for many operations.
# To do:
# JWT authentication

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app.database import get_db_session
from app.config import settings
from app import crud
from app import security
from app.schemas import (
    UserCreateSchema, UserPublicInfoSchema, UserLoginSchema,
    GroupCreateSchema, GroupPublicInfoSchema,
    ExpenseCreateUsingNamesSchema, ExpensePublicInfoSchema, 
    SettlementCreateUsingNamesSchema, SettlementPublicInfoSchema, 
    UserOverallBalanceSchema, BalanceDetailSchema,
    StandardApiResponse, ErrorApiResponse, ApiErrorDetail
)
from app.models import User as UserModel, Group 

api_router = APIRouter()

# Helper to get user ORM by ID, raising 404 if not found
async def get_user_or_404(db: Session, user_id: int, id_type: str = "ID") -> UserModel:
    user = await crud.get_user_by_id_from_db(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with {id_type} {user_id} not found.")
    return user

# Helper to get user ORM by NAME, raising 404 if not found
async def get_user_by_name_or_404(db: Session, user_name: str) -> UserModel:
    user = await crud.get_user_by_name_from_db(db, name=user_name)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with name '{user_name}' not found.")
    return user

# Helper to get group ORM by NAME, raising 404 if not found
async def get_group_by_name_or_404(db: Session, group_name: str) -> Group:
    group = await crud.get_group_by_name_from_db(db, group_name=group_name)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group with name '{group_name}' not found.")
    return group


# === "Authentication" Related Routes (Simplified - NO JWT/Hashing) ===
@api_router.post("/auth/signup", response_model=StandardApiResponse[UserPublicInfoSchema], status_code=status.HTTP_201_CREATED,
    summary="Register User (Unique Username, Plain Password)", tags=["User Management (No Auth/Hashing)"])
async def endpoint_signup_new_user(user_to_create: UserCreateSchema, db: Session = Depends(get_db_session)):
    try:
        new_user_orm = await crud.create_new_user_in_db(db=db, user_data=user_to_create)
    except ValueError as e: # Catch unique username violation from CRUD
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return StandardApiResponse[UserPublicInfoSchema](
        message="User created (WARNING: plain text password, unique username enforced).",
        data=UserPublicInfoSchema.from_orm(new_user_orm))

@api_router.post("/auth/login_basic", response_model=StandardApiResponse[UserPublicInfoSchema],
    summary="Basic Login (Plain Password Check - NO JWT)", tags=["User Management (No Auth/Hashing)"])
async def endpoint_basic_login_check(login_data: UserLoginSchema, db: Session = Depends(get_db_session)):
    user_orm = await crud.get_user_by_email_from_db(db, email=login_data.email)
    if not user_orm or not security.verify_plain_password(login_data.password, user_orm.password_plain):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    return StandardApiResponse[UserPublicInfoSchema](data=UserPublicInfoSchema.from_orm(user_orm))

# === User Routes (No Auth) ===
@api_router.get("/users/name/{user_name}", response_model=StandardApiResponse[UserPublicInfoSchema],
    summary="Get User Details by Unique Name", tags=["User Management (No Auth/Hashing)"])
async def endpoint_get_user_details_by_name(user_name: str, db: Session = Depends(get_db_session)):
    user_orm = await get_user_by_name_or_404(db, user_name)
    return StandardApiResponse[UserPublicInfoSchema](data=UserPublicInfoSchema.from_orm(user_orm))

@api_router.get("/users/id/{user_id}", response_model=StandardApiResponse[UserPublicInfoSchema],
    summary="Get User Details by ID", tags=["User Management (No Auth/Hashing)"])
async def endpoint_get_user_details_by_id(user_id: int, db: Session = Depends(get_db_session)):
    user_orm = await get_user_or_404(db, user_id, "ID")
    return StandardApiResponse[UserPublicInfoSchema](data=UserPublicInfoSchema.from_orm(user_orm))


# === Group Routes (No Auth - Uses Names) ===
@api_router.post("/groups", response_model=StandardApiResponse[GroupPublicInfoSchema], status_code=status.HTTP_201_CREATED,
    summary="Create Group (Specify Creator's Name)", tags=["Groups (No Auth/Hashing)"])
async def endpoint_create_new_group(
    group_to_create: GroupCreateSchema,
    creator_user_name: str = Query(..., description="UNIQUE NAME of the user creating the group"),
    db: Session = Depends(get_db_session)
):
    creator_user_orm = await get_user_by_name_or_404(db, creator_user_name)
    try:
        new_group_orm = await crud.create_group_for_user_in_db(db, group_to_create, creator_user_orm.id)
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return StandardApiResponse[GroupPublicInfoSchema](
        message=f"Group '{new_group_orm.name}' created by '{creator_user_orm.name}'.",
        data=GroupPublicInfoSchema.from_orm(new_group_orm))

@api_router.post("/groups/add_member", response_model=StandardApiResponse[Any],
    summary="Add Member to Group (by Group Name and User Name)", tags=["Groups (No Auth/Hashing)"])
async def endpoint_add_user_to_group_by_name(
    group_name: str = Query(..., description="Name of the group"),
    user_name_to_add: str = Query(..., description="Unique name of the user to add"),
    db: Session = Depends(get_db_session)
):
    try:
        await crud.add_member_to_group_by_names_in_db(db, group_name, user_name_to_add)
    except ValueError as e: # Catch "not found" errors from CRUD
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return StandardApiResponse[Any](message=f"User '{user_name_to_add}' added to group '{group_name}'.")

# === Expense Routes (No Auth - Uses Names) ===
@api_router.post("/expenses", response_model=StandardApiResponse[ExpensePublicInfoSchema], status_code=status.HTTP_201_CREATED,
    summary="Create Expense (Uses Names for Group, Creator, Payers, Sharers)", tags=["Expenses (No Auth/Hashing)"])
async def endpoint_create_new_expense_using_names(
    expense_data_with_names: ExpenseCreateUsingNamesSchema, 
    creator_user_name: str = Query(..., description="Unique NAME of the user creating the expense"),
    db: Session = Depends(get_db_session)
):
    try:
        new_expense_orm = await crud.create_new_expense_using_names_in_db(
            db, expense_data_with_names, creator_user_name
        )
        return StandardApiResponse[ExpensePublicInfoSchema](
            message=f"Expense '{new_expense_orm.description}' recorded by '{creator_user_name}'.",
            data=ExpensePublicInfoSchema.from_orm(new_expense_orm)
        )
    except ValueError as e: 
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@api_router.get("/expenses/user/{user_name}", response_model=StandardApiResponse[List[ExpensePublicInfoSchema]],
    summary="List Expenses Involving a User (by User Name)", tags=["Expenses (No Auth/Hashing)"])
async def endpoint_list_user_involved_expenses_by_name(user_name: str, db: Session = Depends(get_db_session)):
    expenses_list = await crud.get_expenses_involving_user_by_name_from_db(db, user_name)
    if expenses_list is None: 
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{user_name}' not found or has no expenses.")
    return StandardApiResponse[List[ExpensePublicInfoSchema]](
        data=[ExpensePublicInfoSchema.from_orm(exp) for exp in expenses_list]
    )

# === Balance and Settlement Routes (No Auth - Uses Names) ===
@api_router.get("/balances/user/{user_name}", response_model=StandardApiResponse[UserOverallBalanceSchema],
    summary="Get Balance Summary for a User (by User Name)", tags=["Balances & Settlements (No Auth/Hashing)"])
async def endpoint_get_user_balance_summary_by_name(user_name: str, db: Session = Depends(get_db_session)):
    balance_summary_dict = await crud.get_user_overall_balance_summary_by_name_from_db(db, user_name)
    if balance_summary_dict is None: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User '{user_name}' not found for balance summary.")
    try:
        typed_summary = UserOverallBalanceSchema(**balance_summary_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing balance data for '{user_name}': {e}")
    return StandardApiResponse[UserOverallBalanceSchema](data=typed_summary)

@api_router.post("/settle", response_model=StandardApiResponse[SettlementPublicInfoSchema], status_code=status.HTTP_201_CREATED,
    summary="Record Settlement (by User Names)", tags=["Balances & Settlements (No Auth/Hashing)"])
async def endpoint_record_new_settlement_by_names(
    settlement_data_by_names: SettlementCreateUsingNamesSchema, 
    db: Session = Depends(get_db_session)
):
    try:
        new_settlement_orm = await crud.record_new_settlement_by_names_in_db(db, settlement_data_by_names)
        return StandardApiResponse[SettlementPublicInfoSchema](
            message="Settlement recorded.",
            data=SettlementPublicInfoSchema.from_orm(new_settlement_orm)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))