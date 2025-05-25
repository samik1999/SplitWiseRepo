from sqlalchemy.orm import Session
from models import User, Group, GroupMember, Expense, ExpenseSplit, ExpensePayment, Settlement
from schemas import UserCreate, GroupCreate, ExpenseCreate, SettleCreate
from sqlalchemy import func

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_group(db: Session, group: GroupCreate, user_id: int):
    db_group = Group(name=group.name, created_by=user_id)
    db.add(db_group)
    db.commit()
    db.add(GroupMember(group_id=db_group.id, user_id=user_id))
    db.commit()
    return db_group

def add_member_to_group(db: Session, group_id: int, user_id: int):
    db.add(GroupMember(group_id=group_id, user_id=user_id))
    db.commit()
    return {"message": "Member added"}

# Expense
def create_expense(db: Session, expense: ExpenseCreate, user_id: int):
    db_expense = Expense(
        description=expense.description,
        amount=expense.amount,
        group_id=expense.group_id,
        created_by=user_id
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    for p in expense.paid_by:
        db.add(ExpensePayment(expense_id=db_expense.id, paid_by=p.user_id, amount=p.amount))
    for s in expense.split_between:
        db.add(ExpenseSplit(expense_id=db_expense.id, user_id=s.user_id, amount=s.amount, type=expense.type))
    db.commit()
    return db_expense

def get_user_expenses(db: Session, user_id: int):
    splits = db.query(Expense).join(ExpenseSplit).filter(ExpenseSplit.user_id == user_id).all()
    return splits

# Balances
# scalar() doing sum (SELECT SUM(amount) FROM Payment;)
def get_overall_balance(db: Session, user_id: int):
    sent = db.query(func.sum(ExpenseSplit.amount)).filter(ExpenseSplit.user_id == user_id).scalar() or 0
    paid = db.query(func.sum(ExpensePayment.amount)).filter(ExpensePayment.paid_by == user_id).scalar() or 0
    settled = db.query(func.sum(Settlement.amount)).filter(Settlement.from_user == user_id).scalar() or 0
    received = db.query(func.sum(Settlement.amount)).filter(Settlement.to_user == user_id).scalar() or 0
    net = round(paid - sent - received + settled, 2)
    balances = []
    users = db.query(User).filter(User.id != user_id).all()
    for u in users:
        bal = get_balance_between_users(db, user_id, u.id)
        if bal != 0:
            balances.append({"user_id": u.id, "balance": round(bal, 2)})
    return {"total_outstanding": net, "per_user_balance": balances}


def get_balance_between_users(db: Session, uid1: int, uid2: int):
    paid1 = db.query(func.sum(ExpensePayment.amount)).join(Expense).filter(
        ExpensePayment.paid_by == uid1,
        Expense.id == ExpensePayment.expense_id,
        Expense.group_id.in_(
            db.query(GroupMember.group_id).filter(GroupMember.user_id == uid2)
        )
    ).scalar() or 0

    share1 = db.query(func.sum(ExpenseSplit.amount)).filter(ExpenseSplit.user_id == uid1).scalar() or 0

    paid2 = db.query(func.sum(ExpensePayment.amount)).join(Expense).filter(
        ExpensePayment.paid_by == uid2,
        Expense.id == ExpensePayment.expense_id,
        Expense.group_id.in_(
            db.query(GroupMember.group_id).filter(GroupMember.user_id == uid1)
        )
    ).scalar() or 0

    share2 = db.query(func.sum(ExpenseSplit.amount)).filter(ExpenseSplit.user_id == uid2).scalar() or 0

    settlement1 = db.query(func.sum(Settlement.amount)).filter(Settlement.from_user == uid1, Settlement.to_user == uid2).scalar() or 0
    settlement2 = db.query(func.sum(Settlement.amount)).filter(Settlement.from_user == uid2, Settlement.to_user == uid1).scalar() or 0

    return (paid1 - share1 - settlement1) - (paid2 - share2 - settlement2)

# Settle
def settle_balance(db: Session, data: SettleCreate):
    db_settle = Settlement(from_user=data.from_user, to_user=data.to_user, amount=data.amount)
    db.add(db_settle)
    db.commit()
    return db_settle