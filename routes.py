from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud as cd
import models, schemas
from auth import verify_password, create_access_token, get_current_user
from database import get_db

router = APIRouter()

# Auth
@router.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = cd.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return cd.create_user(db, user)

@router.get("/test")
def read_root():
    return {"message": "Hello, World!"}

@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(data={"sub": db_user.id})
    return {"access_token": token, "token_type": "bearer"}

# Groups
@router.post("/groups")
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.create_group(db, group, user.id)

@router.post("/groups/{group_id}/add")
def add_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    return crud.add_member_to_group(db, group_id, user_id)

# Expenses
@router.post("/expenses")
def create_expense(exp: schemas.ExpenseCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.create_expense(db, exp, user.id)

@router.get("/expenses")
def list_expenses(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_user_expenses(db, user.id)

# Balance
@router.get("/balance")
def balance_summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return crud.get_overall_balance(db, user.id)

@router.get("/balance/{user_id}")

def balance_with_user(user_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {"balance": crud.get_balance_between_users(db, user.id, user_id)}

# Settlement
@router.post("/settle")
def settle(settle: schemas.SettleCreate, db: Session = Depends(get_db)):
    return crud.settle_balance(db, settle)
