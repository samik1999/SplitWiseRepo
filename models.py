from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import declarative_base
from datetime import datetime
from pydantic import BaseModel

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

class Group(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_by = Column(Integer, ForeignKey('users.id'))

class GroupMember(Base):
    __tablename__ = 'group_members'

    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

class Expense(Base):
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True)
    description = Column(String)
    amount = Column(Numeric)
    created_by = Column(Integer, ForeignKey('users.id'))
    group_id = Column(Integer, ForeignKey('groups.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

class ExpenseSplit(Base):
    __tablename__ = 'expense_splits'

    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey('expenses.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Numeric)
    type = Column(String)

class ExpensePayment(Base):
    __tablename__ = 'expense_payments'

    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey('expenses.id'))
    paid_by = Column(Integer, ForeignKey('users.id'))
    amount = Column(Numeric)

class Settlement(Base):
    __tablename__ = 'settlements'

    id = Column(Integer, primary_key=True)
    from_user = Column(Integer, ForeignKey('users.id'))
    to_user = Column(Integer, ForeignKey('users.id'))
    amount = Column(Numeric)
    settled_at = Column(DateTime, default=datetime.utcnow)


class UserCreate(BaseModel):
    name: str
    email: str
    password: str