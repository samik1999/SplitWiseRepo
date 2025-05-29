# app/models.py
# Defines database table structures using SQLAlchemy.

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime 

# --- User Model ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False) 
    email = Column(String(100), unique=True, index=True, nullable=False) 
    password_plain = Column(String(255), nullable=False)

# --- Group Model ---
class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False) 
    created_by_id = Column(Integer, ForeignKey('users.id'))
    
# --- GroupMember Model ---
class GroupMember(Base):
    __tablename__ = 'group_members'
    group_id = Column(Integer, ForeignKey('groups.id', ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
    __table_args__ = (UniqueConstraint('group_id', 'user_id', name='uq_group_user_membership'),)


# --- Expense Model ---
class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255))
    amount = Column(Numeric(10, 2))
    created_by_id = Column(Integer, ForeignKey('users.id'))
    group_id = Column(Integer, ForeignKey('groups.id', ondelete="CASCADE")) 
    created_at = Column(DateTime, default=datetime.utcnow)

# --- ExpensePayment Model ---
class ExpensePayment(Base):
    __tablename__ = 'expense_payments'
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey('expenses.id', ondelete="CASCADE"))
    paid_by_user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE")) 
    amount = Column(Numeric(10, 2))
    __table_args__ = (UniqueConstraint('expense_id', 'paid_by_user_id', name='uq_expense_payment_user'),)


# --- ExpenseSplit Model ---
class ExpenseSplit(Base):
    __tablename__ = 'expense_splits'
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey('expenses.id', ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE")) 
    amount = Column(Numeric(10, 2))
    split_type_info = Column(String(50))
    __table_args__ = (UniqueConstraint('expense_id', 'user_id', name='uq_expense_split_user'),)


# --- Settlement Model ---
class Settlement(Base):
    __tablename__ = 'settlements'
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    to_user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    amount = Column(Numeric(10, 2))
    settled_at = Column(DateTime, default=datetime.utcnow)