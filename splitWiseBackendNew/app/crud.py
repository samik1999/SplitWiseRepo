from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, select
from decimal import Decimal
from typing import List, Optional, Dict, Any

from app.models import User, Group, GroupMember, Expense, ExpensePayment, ExpenseSplit, Settlement
from app.schemas import (
    UserCreateSchema, GroupCreateSchema, ExpenseCreateUsingNamesSchema, SettlementCreateUsingNamesSchema,
    UserPublicInfoSchema, ExpensePayerByNameSchema, ExpenseShareByNameSchema # For inputs
)
from app.security import get_password_for_storage, verify_plain_password
from app.redis_utils import (
    retrieve_value_from_cache, store_value_in_cache, remove_value_from_cache,
    generate_cache_key_for_user_details, generate_cache_key_for_user_id_by_email,
    generate_cache_key_for_user_balance_summary
)

def _quantize_amount(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"))

# --- User CRUD Operations ---
async def get_user_by_email_from_db(db: Session, email: str) -> Optional[User]: 
    normalized_email = email.lower()
    stmt = select(User).where(User.email == normalized_email)
    user_orm = db.execute(stmt).scalar_one_or_none()
    if user_orm: 
        await store_value_in_cache(generate_cache_key_for_user_id_by_email(normalized_email), UserPublicInfoSchema.from_orm(user_orm).model_dump())
    return user_orm

async def get_user_by_id_from_db(db: Session, user_id: int) -> Optional[User]: 
    stmt = select(User).where(User.id == user_id)
    user_orm = db.execute(stmt).scalar_one_or_none()
    if user_orm:
        await store_value_in_cache(generate_cache_key_for_user_details(user_orm.id), UserPublicInfoSchema.from_orm(user_orm).model_dump())
    return user_orm

async def get_user_by_name_from_db(db: Session, name: str) -> Optional[User]: 
    """Gets a user by their unique name."""
    stmt = select(User).where(User.name == name) 
    user_orm = db.execute(stmt).scalar_one_or_none()
    return user_orm

async def create_new_user_in_db(db: Session, user_data: UserCreateSchema) -> User:
    existing_user_by_name = await get_user_by_name_from_db(db, name=user_data.name)
    if existing_user_by_name:
        raise ValueError(f"Username '{user_data.name}' is already taken.")
    
    plain_password_to_store = get_password_for_storage(user_data.password)
    new_user_orm = User(
        name=user_data.name, 
        email=user_data.email.lower(),
        password_plain=plain_password_to_store
    )
    db.add(new_user_orm); db.commit(); db.refresh(new_user_orm)
    public_info = UserPublicInfoSchema.from_orm(new_user_orm).model_dump()
    await store_value_in_cache(generate_cache_key_for_user_details(new_user_orm.id), public_info)
    await store_value_in_cache(generate_cache_key_for_user_id_by_email(new_user_orm.email), public_info)
    return new_user_orm

# --- Group CRUD Operations ---
async def get_group_by_name_from_db(db: Session, group_name: str) -> Optional[Group]:
    stmt = select(Group).where(Group.name == group_name)
    return db.execute(stmt).scalar_one_or_none()

async def create_group_for_user_in_db(db: Session, group_data: GroupCreateSchema, creator_user_id: int) -> Group:
    new_group_orm = Group(name=group_data.name, created_by_id=creator_user_id)
    db.add(new_group_orm); db.commit()
    db.add(GroupMember(group_id=new_group_orm.id, user_id=creator_user_id)); db.commit()
    db.refresh(new_group_orm)
    return new_group_orm

async def add_member_to_group_by_names_in_db(db: Session, group_name: str, user_name_to_add: str) -> Optional[GroupMember]:
    """Adds a user (by name) to a group (by name)."""
    target_group = await get_group_by_name_from_db(db, group_name)
    if not target_group: raise ValueError(f"Group '{group_name}' not found.")
    
    user_to_add = await get_user_by_name_from_db(db, user_name_to_add)
    if not user_to_add: raise ValueError(f"User '{user_name_to_add}' not found.")

    stmt_existing = select(GroupMember).where(GroupMember.group_id == target_group.id, GroupMember.user_id == user_to_add.id)
    if db.execute(stmt_existing).scalar_one_or_none():
        return db.execute(stmt_existing).scalar_one_or_none() 

    new_membership = GroupMember(group_id=target_group.id, user_id=user_to_add.id)
    db.add(new_membership); db.commit(); db.refresh(new_membership)
    return new_membership

async def create_new_expense_using_names_in_db(
    db: Session, 
    expense_data_with_names: ExpenseCreateUsingNamesSchema, 
    creator_user_name: str
) -> Expense:
    
    # 1. Resolve creator name to ID
    creator_user = await get_user_by_name_from_db(db, name=creator_user_name)
    if not creator_user: raise ValueError(f"Creator user '{creator_user_name}' not found.")
    creator_user_id = creator_user.id

    # 2. Resolve group name to ID
    target_group = await get_group_by_name_from_db(db, group_name=expense_data_with_names.group_name)
    if not target_group: raise ValueError(f"Group '{expense_data_with_names.group_name}' not found.")
    group_id = target_group.id

    # 3. Resolve user names in paid_by to user IDs
    payer_details_with_ids: List[Dict[str, Any]] = []
    for payer_by_name in expense_data_with_names.paid_by:
        payer_user = await get_user_by_name_from_db(db, name=payer_by_name.user_name)
        if not payer_user: raise ValueError(f"Payer user '{payer_by_name.user_name}' not found.")
        payer_details_with_ids.append({"user_id": payer_user.id, "amount": payer_by_name.amount})
    
    # 4. Resolve user names in split_between to user IDs
    sharer_details_with_ids: List[Dict[str, Any]] = []
    for sharer_by_name in expense_data_with_names.split_between:
        sharer_user = await get_user_by_name_from_db(db, name=sharer_by_name.user_name)
        if not sharer_user: raise ValueError(f"User '{sharer_by_name.user_name}' in split_between not found.")
        sharer_details_with_ids.append({"user_id": sharer_user.id, "amount": sharer_by_name.amount})

    # --- Validation (basic, more can be in Pydantic schemas or routes) ---
    total_paid_from_request = sum(p["amount"] for p in payer_details_with_ids)
    if abs(total_paid_from_request - expense_data_with_names.amount) > Decimal('0.01'):
        raise ValueError("Sum of amounts in 'paid_by' must equal the total expense amount.")

    if expense_data_with_names.split_type == 'manual':
        total_split_from_request = sum(s["amount"] for s in sharer_details_with_ids)
        if abs(total_split_from_request - expense_data_with_names.amount) > Decimal('0.01'):
            raise ValueError("For 'manual' split, sum of 'split_between' amounts must equal total expense amount.")
    elif expense_data_with_names.split_type == 'percentage':
        total_percentage_from_request = sum(s["amount"] for s in sharer_details_with_ids) # amount is percentage here
        if abs(total_percentage_from_request - Decimal('100.00')) > Decimal('0.01'):
             raise ValueError("For 'percentage' split, sum of 'split_between' percentages must be 100%.")

    # --- Create Expense Record ---
    new_expense_orm = Expense(
        description=expense_data_with_names.description,
        amount=_quantize_amount(expense_data_with_names.amount),
        group_id=group_id, 
        created_by_id=creator_user_id 
    )
    db.add(new_expense_orm); db.commit(); db.refresh(new_expense_orm) 

    # --- Record Payments (using resolved IDs) ---
    for payment_detail in payer_details_with_ids:
        db.add(ExpensePayment(expense_id=new_expense_orm.id, paid_by_user_id=payment_detail["user_id"],
                              amount=_quantize_amount(payment_detail["amount"])))

    # --- Record Splits (using resolved IDs) ---
    number_of_sharers = len(sharer_details_with_ids)
    if number_of_sharers == 0:
        db.rollback(); raise ValueError("Expense must be split among at least one user.")

    if expense_data_with_names.split_type == 'equal':
        base_equal_share = _quantize_amount(new_expense_orm.amount / Decimal(number_of_sharers))
        total_allocated = Decimal(0)
        for i, share_detail in enumerate(sharer_details_with_ids):
            actual_share = base_equal_share
            if i == number_of_sharers - 1: actual_share = new_expense_orm.amount - total_allocated
            db.add(ExpenseSplit(expense_id=new_expense_orm.id, user_id=share_detail["user_id"],
                                amount=_quantize_amount(actual_share), split_type_info='equal_share_calculated'))
            total_allocated += _quantize_amount(actual_share)
    elif expense_data_with_names.split_type == 'manual':
        for share_detail in sharer_details_with_ids:
            db.add(ExpenseSplit(expense_id=new_expense_orm.id, user_id=share_detail["user_id"],
                                amount=_quantize_amount(share_detail["amount"]), split_type_info='manual_share_input'))
    elif expense_data_with_names.split_type == 'percentage':
        total_allocated_percentage_amount = Decimal(0)
        for i, share_detail in enumerate(sharer_details_with_ids):
            calculated_share = _quantize_amount((new_expense_orm.amount * share_detail["amount"]) / Decimal(100))
            if i == number_of_sharers - 1: calculated_share = new_expense_orm.amount - total_allocated_percentage_amount
            db.add(ExpenseSplit(expense_id=new_expense_orm.id, user_id=share_detail["user_id"],
                                amount=calculated_share, split_type_info='percentage_share_calculated'))
            total_allocated_percentage_amount += calculated_share
            
    db.commit(); db.refresh(new_expense_orm)

    # Cache Invalidation
    involved_user_ids_for_cache = {creator_user_id}
    involved_user_ids_for_cache.update(p["user_id"] for p in payer_details_with_ids)
    involved_user_ids_for_cache.update(s["user_id"] for s in sharer_details_with_ids)
    for uid in involved_user_ids_for_cache:
        await remove_value_from_cache(generate_cache_key_for_user_balance_summary(uid))
    return new_expense_orm

async def get_expenses_involving_user_by_name_from_db(db: Session, user_name: str) -> List[Expense]:
    user = await get_user_by_name_from_db(db, name=user_name)
    if not user: return []
    return await get_expenses_involving_user_from_db(db, user.id) # Reuse existing ID-based logic

# get_expenses_involving_user_from_db (ID based) remains as before

# --- Balance Calculation ---
async def get_user_overall_balance_summary_by_name_from_db(db: Session, user_name: str) -> Optional[Dict[str, Any]]:
    user = await get_user_by_name_from_db(db, name=user_name)
    if not user: return None 
    # Reuse the ID-based balance calculation
    return await get_user_overall_balance_summary_from_db(db, for_user_id=user.id)

# get_user_overall_balance_summary_from_db (ID based) remains as before

# --- Settlement CRUD Operations ---
async def record_new_settlement_by_names_in_db(db: Session, settlement_data_by_names: SettlementCreateUsingNamesSchema) -> Settlement:
    from_user = await get_user_by_name_from_db(db, name=settlement_data_by_names.from_user_name)
    if not from_user: raise ValueError(f"Payer user '{settlement_data_by_names.from_user_name}' not found.")
    
    to_user = await get_user_by_name_from_db(db, name=settlement_data_by_names.to_user_name)
    if not to_user: raise ValueError(f"Payee user '{settlement_data_by_names.to_user_name}' not found.")

    if from_user.id == to_user.id:
        raise ValueError("Sender and receiver cannot be the same for a settlement.")

    new_settlement_orm = Settlement(
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        amount=_quantize_amount(settlement_data_by_names.amount)
    )
    db.add(new_settlement_orm); db.commit(); db.refresh(new_settlement_orm)

    await remove_value_from_cache(generate_cache_key_for_user_balance_summary(from_user.id))
    await remove_value_from_cache(generate_cache_key_for_user_balance_summary(to_user.id))
    return new_settlement_orm

async def get_expenses_involving_user_from_db(db: Session, user_id_for_expenses: int) -> List[Expense]:
    paid_expense_ids_stmt = select(ExpensePayment.expense_id).distinct().where(ExpensePayment.paid_by_user_id == user_id_for_expenses)
    split_expense_ids_stmt = select(ExpenseSplit.expense_id).distinct().where(ExpenseSplit.user_id == user_id_for_expenses)
    paid_ids = {row[0] for row in db.execute(paid_expense_ids_stmt).all()}
    split_ids = {row[0] for row in db.execute(split_expense_ids_stmt).all()}
    all_relevant_expense_ids = paid_ids.union(split_ids)
    if not all_relevant_expense_ids: return []
    stmt = select(Expense).where(Expense.id.in_(all_relevant_expense_ids)).order_by(Expense.created_at.desc())
    return list(db.execute(stmt).scalars().all())

async def get_user_overall_balance_summary_from_db(db: Session, for_user_id: int) -> Dict[str, Any]:
    cache_key = generate_cache_key_for_user_balance_summary(for_user_id)
    cached_summary = await retrieve_value_from_cache(cache_key)
    if cached_summary: return cached_summary
    net_balance_with_each_other_user: Dict[int, Decimal] = {}
    all_expenses_stmt = select(Expense)
    all_expenses = db.execute(all_expenses_stmt).scalars().all()
    for expense in all_expenses:
        user_paid_for_this_expense = Decimal(0)
        stmt_user_payment = select(func.sum(ExpensePayment.amount)).where(
            ExpensePayment.expense_id == expense.id, ExpensePayment.paid_by_user_id == for_user_id)
        user_payment_sum = db.execute(stmt_user_payment).scalar_one_or_none()
        if user_payment_sum: user_paid_for_this_expense = user_payment_sum
        user_share_of_this_expense = Decimal(0)
        stmt_user_share = select(ExpenseSplit.amount).where(
            ExpenseSplit.expense_id == expense.id, ExpenseSplit.user_id == for_user_id)
        user_share_amount = db.execute(stmt_user_share).scalar_one_or_none()
        if user_share_amount: user_share_of_this_expense = user_share_amount
        net_contribution_for_expense = user_paid_for_this_expense - user_share_of_this_expense
        if net_contribution_for_expense > Decimal(0):
            stmt_other_sharers = select(ExpenseSplit.user_id, ExpenseSplit.amount).where(
                ExpenseSplit.expense_id == expense.id, ExpenseSplit.user_id != for_user_id)
            other_sharers_of_this_expense = db.execute(stmt_other_sharers).all()
            total_other_shares_amount = sum(s.amount for s in other_sharers_of_this_expense)
            if total_other_shares_amount > Decimal(0):
                for other_sharer in other_sharers_of_this_expense:
                    amount_owed_by_other_sharer_to_for_user = \
                        (other_sharer.amount / total_other_shares_amount) * net_contribution_for_expense
                    net_balance_with_each_other_user[other_sharer.user_id] = \
                        net_balance_with_each_other_user.get(other_sharer.user_id, Decimal(0)) + _quantize_amount(amount_owed_by_other_sharer_to_for_user)
        elif net_contribution_for_expense < Decimal(0):
            amount_borrowed_by_for_user = abs(net_contribution_for_expense)
            stmt_other_payers = select(ExpensePayment.paid_by_user_id, ExpensePayment.amount).where(
                ExpensePayment.expense_id == expense.id, ExpensePayment.paid_by_user_id != for_user_id)
            other_payers_of_this_expense = db.execute(stmt_other_payers).all()
            total_other_payments_amount = sum(p.amount for p in other_payers_of_this_expense)
            if total_other_payments_amount > Decimal(0):
                for other_payer in other_payers_of_this_expense:
                    amount_for_user_owes_to_other_payer = \
                        (other_payer.amount / total_other_payments_amount) * amount_borrowed_by_for_user
                    net_balance_with_each_other_user[other_payer.paid_by_user_id] = \
                        net_balance_with_each_other_user.get(other_payer.paid_by_user_id, Decimal(0)) - _quantize_amount(amount_for_user_owes_to_other_payer)
    stmt_settlements_sent_by_user = select(Settlement.to_user_id, Settlement.amount)\
        .where(Settlement.from_user_id == for_user_id)
    for to_user_id_val, amount_val in db.execute(stmt_settlements_sent_by_user).all():
        net_balance_with_each_other_user[to_user_id_val] = \
            net_balance_with_each_other_user.get(to_user_id_val, Decimal(0)) - _quantize_amount(amount_val)
    stmt_settlements_received_by_user = select(Settlement.from_user_id, Settlement.amount)\
        .where(Settlement.to_user_id == for_user_id)
    for from_user_id_val, amount_val in db.execute(stmt_settlements_received_by_user).all():
        net_balance_with_each_other_user[from_user_id_val] = \
            net_balance_with_each_other_user.get(from_user_id_val, Decimal(0)) + _quantize_amount(amount_val)
    total_user_owes_overall = Decimal(0); total_owed_to_user_overall = Decimal(0)
    balance_details_list: List[Dict[str, Any]] = []
    for other_user_id_val, net_amount_with_other in net_balance_with_each_other_user.items():
        if net_amount_with_other == Decimal(0) or other_user_id_val == for_user_id: continue
        quantized_net_amount = _quantize_amount(net_amount_with_other)
        balance_details_list.append({ "other_user_id": other_user_id_val, "balance_amount": quantized_net_amount })
        if quantized_net_amount > 0: total_owed_to_user_overall += quantized_net_amount
        else: total_user_owes_overall += abs(quantized_net_amount)
    final_net_balance_for_user = _quantize_amount(total_owed_to_user_overall - total_user_owes_overall)
    summary_to_cache_and_return = {
        "net_total_balance": final_net_balance_for_user,
        "balance_with_each_user": balance_details_list }
    await store_value_in_cache(cache_key, summary_to_cache_and_return)
    return summary_to_cache_and_return