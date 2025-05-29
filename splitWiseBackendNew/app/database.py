# app/database.py
# This file handles database connection setup and session management using SQLAlchemy.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base 
from app.config import settings

# Special arguments for SQLite (allows multiple threads to use the same connection)
engine_connection_args = {}
if settings.DATABASE_URL and settings.DATABASE_URL.startswith("sqlite"):
    engine_connection_args["connect_args"] = {"check_same_thread": False}

try:
    db_engine = create_engine(
        settings.DATABASE_URL,
        **engine_connection_args
    )
    print(f"Database engine created for URL: {settings.DATABASE_URL}")
except Exception as e:
    print(f"Error creating database engine: {e}")
    db_engine = None 


if db_engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
else:
    SessionLocal = None # No sessions if engine failed
    print("Warning: SessionLocal not created because database engine initialization failed.")

Base = declarative_base()


# --- Dependency for FastAPI Routes ---
def get_db_session():
    if SessionLocal is None:
        raise RuntimeError("Database session factory (SessionLocal) is not initialized. Check database configuration and connection.")
    
    db = SessionLocal() 
    try:
        yield db 
    finally:
        db.close() 

# --- Function to Create Database Tables ---
def initialize_database_tables():
   
    if db_engine is None:
        print("Cannot create database tables: Database engine is not initialized.")
        return
    try:
        print("Initializing database tables (if they don't exist)...")
        Base.metadata.create_all(bind=db_engine) 
        print("Database tables checked/created.")
    except Exception as e:
        print(f"An error occurred while creating database tables: {e}")