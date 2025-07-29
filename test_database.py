#!/usr/bin/env python3
"""
Simple test script to verify database connection and basic functionality.
"""

import asyncio
import os
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://genomics_user:Boolmind2025%40%40@localhost:5432/genomics_platform"

async def test_database_connection():
    """Test database connection and basic operations."""
    print("Testing database connection...")
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Database connected successfully!")
            print(f"PostgreSQL version: {version}")
            
            # Check tables
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Tables found: {tables}")
            
            # Check datasets table
            result = conn.execute(text("SELECT * FROM datasets;"))
            datasets = result.fetchall()
            print(f"✅ Datasets in database: {len(datasets)}")
            for dataset in datasets:
                print(f"  - {dataset[1]} ({dataset[2]})")
                
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_simple_data_insertion():
    """Test simple data insertion into the database."""
    print("\nTesting data insertion...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Create some test data
        test_variants = [
            {
                "variant_id": "test_001",
                "chromosome": "chr1",
                "position": 1000,
                "reference_allele": "A",
                "alternate_allele": "T",
                "gene_id": "GENE001",
                "clinical_significance": "benign",
                "dataset_id": "test_dataset"
            },
            {
                "variant_id": "test_002", 
                "chromosome": "chr2",
                "position": 2000,
                "reference_allele": "C",
                "alternate_allele": "G",
                "gene_id": "GENE002",
                "clinical_significance": "pathogenic",
                "dataset_id": "test_dataset"
            }
        ]
        
        # Insert test data
        with engine.connect() as conn:
            for variant in test_variants:
                conn.execute(text("""
                    INSERT INTO variants (variant_id, chromosome, position, reference_allele, 
                                        alternate_allele, gene_id, clinical_significance, dataset_id)
                    VALUES (:variant_id, :chromosome, :position, :reference_allele,
                           :alternate_allele, :gene_id, :clinical_significance, :dataset_id)
                """), variant)
            conn.commit()
            
        print("✅ Test data inserted successfully!")
        
        # Verify insertion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM variants WHERE dataset_id = 'test_dataset';"))
            count = result.fetchone()[0]
            print(f"✅ Test variants count: {count}")
            
        return True
        
    except Exception as e:
        print(f"❌ Data insertion failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🧬 Genomics Platform Database Test")
    print("=" * 50)
    
    # Test database connection
    db_ok = await test_database_connection()
    
    if db_ok:
        # Test data insertion
        await test_simple_data_insertion()
        
        print("\n🎉 Database test completed successfully!")
        print("The database is ready for data pipeline operations.")
    else:
        print("\n❌ Database test failed!")
        print("Please check your Docker services and database configuration.")

if __name__ == "__main__":
    asyncio.run(main()) 