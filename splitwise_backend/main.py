from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import schemas
import models as model
import crud as crud

Base = declarative_base()

DATABASE_URL = "sqlite:///./test.db"  #

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

# Create the tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(model.User).filter(model.User.id == user_id).first()

@app.post("/signup")
def signup(user: model.UserCreate, db: Session = Depends(get_db)):
    db_user = model.User(name=user.name, email=user.email, password_hash=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login")
def login(user: model.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(model.User).filter(model.User.email == user.email).first()
    if not db_user or db_user.password_hash != user.password:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    return {"message": f"Welcome back, {db_user.name}!"}

@app.post("/groups")
def create_group(group: schemas.GroupCreate, db: Session = Depends(get_db)):
    db_group = model.Group(name=group.name, created_by=group.user)
    db.add(db_group)
    db.commit()
    db.add(model.GroupMember(group_id=db_group.id, user_id=group.user))
    db.commit()
    return db_group

@app.post("/groups/{group_id}/{user_id}/add")
def add_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    return crud.add_member_to_group(db, group_id, user_id)

@app.post("/expenses")
def create_expense(exp: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    return crud.create_expense(db, exp, exp.user)

@app.get("/expenses/{user_id}/")
def list_expenses(user_id:int,db: Session = Depends(get_db)):
    return crud.get_user_expenses(db, user_id)

@app.get("/balance/{user}")
def balance_summary(user:int,db: Session = Depends(get_db)):
    return crud.get_overall_balance(db, user)

@app.post("/settle")
def settle(settle: schemas.SettleCreate, db: Session = Depends(get_db)):
    return crud.settle_balance(db, settle)
