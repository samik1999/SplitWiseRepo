# SplitWiseRepo(Just diving into my first FastAPI project—excited to see how it goes!)
A minimal backend clone of Splitwise using FastAPI and SQLite. Users can sign up, create groups, add members, add expenses, settle balances, and get a complete balance summary.

# Local Development Setup (Please follow the steps to run application in local (Python 3.9.6 version is required)
# Step 1: Clone the Repository and checkout feature/SplitWiseBackend
git clone https://github.com/samik1999/SplitWiseRepo.git
cd SplitWiseRepo
git checkout "feature/SplitWiseBackend"

# Step 2: Create a Virtual Environment and Activate It
python3 -m venv venv         
source venv/bin/activate    

# Step 3: Install the Requirements
pip3 install -r requirements.txt

# Step 4: Run the FastAPI Application
python3 -m uvicorn main:app --reload --port 8080
# This will:
# Start the API on http://localhost:8080
# Automatically create the necessary tables in the test.db SQLite database

# Command to see table data (go to database and run select queries)
  sqlite3 test.db
  
# Table Schemas
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password_hash TEXT
);

-- groups
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    created_by INTEGER REFERENCES users(id)
);

-- group_members
CREATE TABLE group_members (
    group_id INTEGER REFERENCES groups(id),
    user_id INTEGER REFERENCES users(id),
    PRIMARY KEY (group_id, user_id)
);

-- expenses
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    description TEXT,
    amount NUMERIC,
    created_by INTEGER REFERENCES users(id),
    group_id INTEGER REFERENCES groups(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- expense_splits
CREATE TABLE expense_splits (
    id SERIAL PRIMARY KEY,
    expense_id INTEGER REFERENCES expenses(id),
    user_id INTEGER REFERENCES users(id),
    amount NUMERIC,
    type VARCHAR(20) -- 'equal', 'manual', 'percentage'
);

-- expense_payments
CREATE TABLE expense_payments (
    id SERIAL PRIMARY KEY,
    expense_id INTEGER REFERENCES expenses(id),
    paid_by INTEGER REFERENCES users(id),
    amount NUMERIC
);

-- settlements
CREATE TABLE settlements (
    id SERIAL PRIMARY KEY,
    from_user INTEGER REFERENCES users(id),
    to_user INTEGER REFERENCES users(id),
    amount NUMERIC,
    settled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# API Endpoints

# User
# Signup
# POST /signup
# Request Body:
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "password123"
}

# Login (no auth)
# POST /login
# Request Body:
{
  "email": "alice@example.com",
  "password": "password123"
}

# Groups
# Create Group
# POST /groups
{
  "name": "Trip to Goa",
  "user": 1
}

# Expenses
# Create Expense
# POST /expenses
{
  "user": 1,
  "group_id": 1,
  "description": "Hotel",
  "total_amount": 1000,
  "splits": [
  {"user_id": 1, "amount": 500},
   {"user_id": 2, "amount": 500}]
}

# Balances
# Get Balance Summary
# GET /balance/{user_id}

# Settlement
# Settle Balance
# POST /settle
{
  "from_user": 2,
  "to_user": 1,
  "amount": 500
}


