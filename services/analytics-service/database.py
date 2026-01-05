from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database configuration
DB_NAME = os.getenv("ANALYTICS_DB_NAME", "analytics_db")
DB_USER = os.getenv("ANALYTICS_DB_USER", "postgres")
DB_PASSWORD = os.getenv("ANALYTICS_DB_PASSWORD", "postgres")
DB_HOST = os.getenv("ANALYTICS_DB_HOST", "localhost")
DB_PORT = os.getenv("ANALYTICS_DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
