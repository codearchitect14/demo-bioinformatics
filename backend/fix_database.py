#!/usr/bin/env python3
"""
Fix database schema by recreating tables with correct structure
"""

from app.database import engine, get_db, Base
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Recreate database tables with correct schema."""
    try:
        print("🔧 Fixing database schema...")
        
        # Drop all tables
        print("📥 Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        # Create all tables with correct schema
        print("📤 Creating new tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database schema fixed successfully!")
        
        # Test database connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) FROM variants"))
            count = result.fetchone()[0]
            print(f"📊 Variants table now has {count} records")
            
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        raise

if __name__ == "__main__":
    fix_database_schema() 