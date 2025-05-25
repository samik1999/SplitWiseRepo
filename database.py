



# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from urllib.parse import quote_plus

# # URL components
# username = "samiksha.bidua"
# password = quote_plus("Simmi@123")  # URL-encode special characters like @
# host = "localhost"
# port = 5434
# database = "splitwise_clone"

# # Async DB URL for asyncpg
# DATABASE_URL = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"

# # Create async engine
# async_engine = create_async_engine(DATABASE_URL, echo=True)

# # Async session factory
# AsyncSessionLocal = sessionmaker(
#     bind=async_engine,
#     class_=AsyncSession,
#     expire_on_commit=False
# )

# # Base class for all models
# Base = declarative_base()

# # Dependency for FastAPI
# async def get_db():
#     async with AsyncSessionLocal() as session:
#         yield session






# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import sessionmaker

# DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/mydb"

# # Create the async engine
# engine = create_async_engine(DATABASE_URL, echo=True)

# # Create a sessionmaker for AsyncSession
# async_session = sessionmaker(
#     engine, class_=AsyncSession, expire_on_commit=False
# )

# # Dependency
# async def get_db():
#     async with async_session() as session:
#         yield session





# import psycopg
# from psycopg_pool import ConnectionPool

# # Connection string (DSN) for your PostgreSQL database
# DATABASE_DSN = "host=localhost port=5434 dbname=splitwise_clone user=samiksha.bidua password=Simmi@123"

# # Create a global connection pool (like the SQLAlchemy engine)
# pool = ConnectionPool(DATABASE_DSN)

# # Dependency function for FastAPI routes
# def get_db():
#     with pool.connection() as conn:
#         yield conn  # yield the connection for use in the route



# import psycopg


# def get_db():
#     # Create and return a new connection each time
#     # or you can make this return a connection pool connection for better performance
#     return psycopg.connect(
#         host="your_host",
#         port=5432,
#         dbname="your_dbname",
#         user="your_username",
#         password="your_password"
#     )

# try:
#     # Connect to your PostgreSQL database
#     with psycopg.connect(
#         host="your_host",
#         port=5432,
#         dbname="your_dbname",
#         user="your_username",
#         password="your_password"
#     ) as conn:
#         with conn.cursor() as cur:
#             cur.execute("SELECT version();")
#             version = cur.fetchone()
#             print("Database version:", version)

# except Exception as e:
#     print("Error connecting to PostgreSQL:", e)




# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker, declarative_base
# import asyncio

# DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5434/splitwise_clone"

# engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# AsyncSessionLocal = sessionmaker(
#     bind=engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autoflush=False,
#     autocommit=False,
# )

# Base = declarative_base()

# async def get_db():
#     async with AsyncSessionLocal() as session:
#         yield session

# # New function to create tables asynchronously
# async def init_db():
#     async with engine.begin() as conn:
#         # This runs the synchronous metadata.create_all() in an async context
#         await conn.run_sync(Base.metadata.create_all)

# # Optionally, run this when the module is run directly, or call it from your startup event
# if __name__ == "__main__":
#     asyncio.run(init_db())




# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker, declarative_base

# DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5434/splitwise_clone"

# engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# AsyncSessionLocal = sessionmaker(
#     bind=engine,
#     class_=AsyncSession,
#     expire_on_commit=False,
#     autoflush=False,
#     autocommit=False,
# )

# Base = declarative_base()

# async def get_db():
#     async with AsyncSessionLocal() as session:
#         yield session







# database.py

# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# # Set your actual PostgreSQL database URL here
# # Format: postgresql://username:password@host:port/database_name
# DATABASE_URL = "postgresql://samiksha.bidua:Simmi@123@localhost:5434/splitwise_clone"

# # Create the SQLAlchemy engine
# engine = create_engine(DATABASE_URL)

# # Create a configured session class
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Base class for all models to inherit from
# Base = declarative_base()

# # Dependency function for FastAPI routes
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
