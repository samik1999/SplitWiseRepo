# SplitWiseRepo
A minimal backend clone of Splitwise using FastAPI and SQLite. Users can sign up, create groups, add members, add expenses, settle balances, and get a complete balance summary.
# ToDo's
1- Implement JWT Token Logic for maintaining session
2- Implement Redis for caching frequently access splits, user details and login
3- Set Up a Database Before Running a Script

# Local Development Setup
# Step 1: Clone the Repository
git clone https://github.com/yourusername/SplitWiseRepo.git
cd SplitWiseRepo

# Step 2: Create a Virtual Environment and Activate It
python3 -m venv venv         
source venv/bin/activate    

# Step 3: Install the Requirements
pip3 install -r requirements.txt

# Step 4: Run the FastAPI Application
uvicorn main:app --reload --port 8080
# This will:
# Start the API on http://localhost:8080
# Automatically create the necessary tables in the test.db SQLite database

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


