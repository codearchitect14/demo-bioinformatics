#!/usr/bin/env python3
"""
Database Analysis Script

Analyze the database schema and data to understand the structure for ML model development.
"""

import psycopg2
import json
from typing import Dict, List, Any

def analyze_database():
    """Analyze the database schema and data."""
    
    # Database connection
    conn = psycopg2.connect('postgresql://genomics_user:Boolmind2025%40%40@localhost:5432/genomics_platform')
    cur = conn.cursor()
    
    # Tables to analyze
    tables = ['variants', 'gene_expression', 'drug_targets', 'literature_entities', 'samples', 'datasets']
    
    analysis = {}
    
    for table in tables:
        print(f"\n=== Analyzing {table} table ===")
        
        # Get column information
        cur.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        print(f"Columns in {table}:")
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"Total rows: {count}")
        
        # Get sample data
        if count > 0:
            cur.execute(f"SELECT * FROM {table} LIMIT 3")
            sample_data = cur.fetchall()
            
            # Get column names
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position")
            col_names = [row[0] for row in cur.fetchall()]
            
            print("Sample data:")
            for i, row in enumerate(sample_data):
                print(f"  Row {i+1}:")
                for j, value in enumerate(row):
                    print(f"    {col_names[j]}: {value}")
        
        # Store analysis
        analysis[table] = {
            'columns': [{'name': col[0], 'type': col[1], 'nullable': col[2]} for col in columns],
            'count': count,
            'sample_data': sample_data if count > 0 else []
        }
    
    conn.close()
    
    # Save analysis to file
    with open('database_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\n=== Database Analysis Complete ===")
    print(f"Analysis saved to database_analysis.json")
    
    return analysis

if __name__ == "__main__":
    analyze_database() 