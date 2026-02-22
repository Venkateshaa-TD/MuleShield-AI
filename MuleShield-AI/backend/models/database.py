"""
MuleShield AI - Database Configuration
SQLite database setup for mock AML data storage
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database URL - stored in local file for demo purposes
DATABASE_URL = "sqlite:///./muleshield.db"

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False  # Set to True for SQL query logging
)

# Session factory for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    Dependency injection for database sessions.
    Ensures proper session cleanup after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in the models.
    """
    from . import schemas  # Import to register models
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")
