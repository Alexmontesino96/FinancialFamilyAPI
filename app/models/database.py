"""
Database Configuration Module

This module sets up the SQLAlchemy database connection and session management.
It configures the database engine, session factory, and base model class.

The database URL is read from environment variables, with a default value
provided for development environments.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
  
# Get database URL from environment variables with a default fallback
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set in environment variables. This is required for database connection.")

# Limpiar la URL de posibles caracteres de nueva línea u otros caracteres no deseados
DATABASE_URL = DATABASE_URL.strip()

# Create database engine with the configured URL
engine = create_engine(DATABASE_URL)

# Create session factory for database interactions
# autocommit=False: Transactions must be explicitly committed
# autoflush=False: Changes won't be automatically flushed to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative model definitions
Base = declarative_base()

def get_db():
    """
    Database session dependency.
    
    Creates a new database session for each request and closes it when the request is done.
    This function is used as a FastAPI dependency to provide database sessions to route handlers.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Ensure the database session is closed even if an exception occurs
        db.close() 