#!/usr/bin/env python3
"""
Repopulate database with sample data after schema fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from populate_complete_database import run_complete_population

def main():
    """Repopulate the database with all datasets."""
    print("🔄 Repopulating database with correct schema...")
    
    try:
        # Run the complete population
        run_complete_population()
        
        print("✅ Database repopulated successfully!")
        print("📊 All datasets are now available through the API")
        
    except Exception as e:
        print(f"❌ Error repopulating database: {e}")
        raise

if __name__ == "__main__":
    main() 