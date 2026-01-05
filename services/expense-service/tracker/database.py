from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker 
from dotenv import load_dotenv
import os 

load_dotenv()

# Database configuration
DB_NAME = os.getenv("EXPENSE_DB_NAME", "expense_db")
DB_USER = os.getenv("EXPENSE_DB_USER", "postgres")
DB_PASSWORD = os.getenv("EXPENSE_DB_PASSWORD", "postgres")
DB_HOST = os.getenv("EXPENSE_DB_HOST", "localhost")
DB_PORT = os.getenv("EXPENSE_DB_PORT", "5432")

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close()