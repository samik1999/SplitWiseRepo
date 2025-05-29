from typing import Optional
from app.config import settings

def verify_plain_password(plain_password_submitted: str, plain_password_in_db: str) -> bool:
    if not plain_password_submitted or not plain_password_in_db:
        return False
    return plain_password_submitted == plain_password_in_db

def get_password_for_storage(password: str) -> str:
    print("SECURITY WARNING: Password hashing is disabled! Storing plain text password.")
    return password 
