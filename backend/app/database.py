#!/usr/bin/env python3
"""
Database Configuration and Connection Management

Handles database connection, session management, and connection pooling
for the genomics platform PostgreSQL database.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging
from typing import Generator
import os

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql://genomics_user:Boolmind2025%40%40@localhost:5432/genomics_platform"

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections that can be created
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Session: Database session
        
    Example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def test_database_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get database information and statistics.
    
    Returns:
        dict: Database information
    """
    try:
        with engine.connect() as connection:
            # Get database version
            version_result = connection.execute(text("SELECT version()"))
            version = version_result.fetchone()[0]
            
            # Get table counts
            tables = [
                "datasets", "variants", "samples", "gene_expression",
                "literature_entities", "drug_targets", "analysis_jobs", "model_predictions"
            ]
            
            table_counts = {}
            for table in tables:
                try:
                    count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    table_counts[table] = count_result.fetchone()[0]
                except Exception as e:
                    logger.warning(f"Could not get count for table {table}: {e}")
                    table_counts[table] = 0
            
            return {
                "version": version,
                "table_counts": table_counts,
                "connection_pool": {
                    "pool_size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow()
                }
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"error": str(e)}


# Initialize database tables
def init_db():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise


if __name__ == "__main__":
    # Test database connection
    if test_database_connection():
        print("✅ Database connection successful")
        info = get_database_info()
        print(f"📊 Database info: {info}")
    else:
        print("❌ Database connection failed") 