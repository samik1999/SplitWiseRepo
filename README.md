# SplitWiseRepo(Just diving into my first FastAPI project—excited to see how it goes!)
A minimal backend clone of Splitwise using FastAPI and SQLite. Users can sign up, create groups, add members, add expenses, settle balances, and get a complete balance summary.

# Local Development Setup Follow these steps to run the application on your local machine. (Python 3.8+ is recommended)
# Step 1: Clone the Repository 
git clone https://github.com/samik1999/SplitWiseRepo.git
# Step 2:
cd SplitWiseRepo
# Step 3: checkout feature/SplitWiseBackend
git checkout "feature/SpliWiseBackend"
# step 4: 
cd splitWiseBackendNew

# Step 5: Create a Virtual Environment and Activate It
python3 -m venv venv         
source venv/bin/activate    

# Step 6: Install the Requirements
pip3 install -r requirements.txt

# Step 7: Ensure Redis Server is Running
This application uses Redis for caching. Make sure your Redis server is running.
macOS (with Homebrew): redis-server (to run in foreground) or brew services start redis (to run in background).

# Step 7: Run the FastAPI Application
python3 -m uvicorn main:app --reload --port 8080

<!-- This will:

Start the API server on http://localhost:8080.
Create the minimal_splitwise.db SQLite database file (if it doesn't exist) and the necessary tables when the application first starts up.
You can access the API documentation (Swagger UI) at http://localhost:8080/api/v1/docs.  -->

# Command to see table data (go to database and run select queries)
  sqlite3 minimal_splitwise.db
  
# Table Schemas
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE, -- Usernames are unique
    email VARCHAR(100) NOT NULL UNIQUE,
    password_plain VARCHAR(255) NOT NULL -- WARNING: Stores plain text passwords
);

CREATE TABLE groups (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    created_by_id INTEGER,
    FOREIGN KEY(created_by_id) REFERENCES users (id)
);

CREATE TABLE group_members (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (group_id, user_id),
    FOREIGN KEY(group_id) REFERENCES groups (id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE expenses (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    description VARCHAR(255),
    amount NUMERIC(10, 2), -- Storing amounts with 2 decimal places
    created_by_id INTEGER,
    group_id INTEGER,
    created_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')), -- SQLite way for default timestamp
    FOREIGN KEY(created_by_id) REFERENCES users (id),
    FOREIGN KEY(group_id) REFERENCES groups (id) ON DELETE CASCADE
);

CREATE TABLE expense_payments (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER,
    paid_by_user_id INTEGER,
    amount NUMERIC(10, 2),
    FOREIGN KEY(expense_id) REFERENCES expenses (id) ON DELETE CASCADE,
    FOREIGN KEY(paid_by_user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (expense_id, paid_by_user_id) -- Assuming one payment entry per user for an expense
);

CREATE TABLE expense_splits (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER,
    user_id INTEGER,
    amount NUMERIC(10, 2),
    split_type_info VARCHAR(50), -- e.g., 'equal_share_calculated'
    FOREIGN KEY(expense_id) REFERENCES expenses (id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (expense_id, user_id) -- Assuming one split entry per user for an expense
);

CREATE TABLE settlements (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    from_user_id INTEGER,
    to_user_id INTEGER,
    amount NUMERIC(10, 2),
    settled_at DATETIME DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
    FOREIGN KEY(from_user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY(to_user_id) REFERENCES users (id) ON DELETE CASCADE
);

<!-- API Endpoints (Simplified - No JWT/Hashing)
Base URL: http://localhost:8080/api/v1

User Management
Signup (Create User)
Endpoint: POST /auth/signup
Request Body: -->
{
  "name": "AliceWonder", // Username must be unique
  "email": "alice.wonder@example.com",
  "password": "password123" 
}

<!-- Basic Login Check 
Endpoint: POST /auth/login_basic
Request Body: -->
{
  "email": "alice.wonder@example.com",
  "password": "password123"
}
<!-- Success Response: User's public info if credentials match. -->


<!-- Get User by Unique Name
Endpoint: GET /users/name/{user_name}
Example: GET /users/name/AliceWonder
Get User by ID
Endpoint: GET /users/id/{user_id}
Example: GET /users/id/1
Groups
Create Group
Endpoint: POST /groups
Query Parameter: creator_user_name (string, required, e.g., ?creator_user_name=AliceWonder)
Request Body: -->

{
  "name": "Wonderland Trip Fund"
}

<!-- Add Member to Group
Endpoint: POST /groups/add_member
Query Parameters:
group_name (string, required, e.g., ?group_name=Wonderland%20Trip%20Fund)
user_name_to_add (string, required, e.g., &user_name_to_add=MadHatter)
Request Body: (Empty)
Expenses
Create Expense
Endpoint: POST /expenses
Query Parameter: creator_user_name (string, required, e.g., ?creator_user_name=AliceWonder)
Request Body (ExpenseCreateUsingNamesSchema): -->

{
  "description": "Tea Party Supplies",
  "amount": 150.75,
  "group_name": "Wonderland Trip Fund",
  "paid_by": [
    {
      "user_name": "AliceWonder",
      "amount": 100.75
    },
    {
      "user_name": "MadHatter",
      "amount": 50.00
    }
  ],
  "split_between": [
    {
      "user_name": "AliceWonder",
      "amount": 75.38  // Or 1 for 'equal' if backend recalculates
    },
    {
      "user_name": "MadHatter",
      "amount": 75.37  // Or 1 for 'equal'
    }
  ],
  "split_type": "equal" // "equal", "manual", or "percentage"
}

<!-- List Expenses Involving a User
Endpoint: GET /expenses/user/{user_name}
Example: GET /expenses/user/AliceWonder
Balances & Settlements
Get User's Balance Summary
Endpoint: GET /balances/user/{user_name}
Example: GET /balances/user/AliceWonder
Settle Balance
Endpoint: POST /settle
Request Body (SettlementCreateUsingNamesSchema): -->
{
  "from_user_name": "MadHatter",
  "to_user_name": "AliceWonder",
  "amount": 25.50
}

<!-- #Functionality of Each File (in app/) -->
<!-- main.py: -->

This is the entry point that starts the FastAPI application.
It initializes the app, sets up global configurations (like startup/shutdown events for database & Redis).
It includes all the API routes defined in routers.py.
Defines custom exception handlers to ensure consistent error responses.
<!-- routers.py: -->

Defines all the specific API paths (endpoints) like /auth/signup, /groups, /expenses.
Handles incoming HTTP requests, validates request data using schemas from schemas.py.
Calls functions from crud.py to interact with the database.

<!-- crud.py: -->

This file contains all the functions that directly interact with the database.
Also interacts with redis_utils.py for caching or invalidating cached data.
<!-- schemas.py: -->

Defines the structure and data types for API requests and responses using Pydantic models.
Ensures that incoming data is valid before it's processed.
Helps in serializing data (converting Python objects to JSON) for responses.
Includes the standard API response structures (StandardApiResponse, ErrorApiResponse).
<!-- models.py: -->

Defines the database table structures using SQLAlchemy ORM 
Each class in this file  maps to a table in your SQLite database.

<!-- security.py: -->

In the current simplified version, this file mainly handles password verification (plain text comparison, as hashing was removed for debugging).

<!-- redis_utils.py: -->

Manages the connection to your Redis server (for caching).

<!-- database.py: -->

Sets up the connection to your database (SQLite in this case) using the DATABASE_URL from config.py.
Provides the SessionLocal factory for creating database sessions (which crud.py uses to talk to the database).

<!-- config.py: -->
Manages all application settings and configurations.

