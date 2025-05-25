-- users
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
