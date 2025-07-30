import psycopg2
import json
from datetime import datetime

def check_database_data():
    try:
        # Connect to database with correct credentials
        conn = psycopg2.connect('postgresql://genomics_user:Boolmind2025%40%40@localhost:5432/genomics_platform')
        cur = conn.cursor()
        
        print("🔍 Checking Database Tables and Data...")
        print("=" * 50)
        
        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cur.fetchall()
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            print(f"\n📋 Table: {table_name}")
            
            # Get row count
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"   Rows: {count}")
            
            # Get column info
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            print(f"   Columns: {len(columns)}")
            
            # Show sample data if table has data
            if count > 0:
                cur.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = cur.fetchall()
                print(f"   Sample data (first 3 rows):")
                for i, row in enumerate(sample_data, 1):
                    print(f"     Row {i}: {row}")
            else:
                print("   No data available")
        
        # Check specific data for frontend
        print("\n" + "=" * 50)
        print("🎯 Frontend Data Analysis:")
        
        # Variants data
        cur.execute("SELECT COUNT(*) FROM variants")
        variant_count = cur.fetchone()[0]
        print(f"🧬 Variants: {variant_count}")
        
        if variant_count > 0:
            cur.execute("""
                SELECT chromosome, COUNT(*) as count, 
                       AVG(CAST(quality_score AS FLOAT)) as avg_quality
                FROM variants 
                GROUP BY chromosome 
                ORDER BY count DESC 
                LIMIT 5
            """)
            variant_stats = cur.fetchall()
            print("   Top chromosomes by variant count:")
            for chrom, count, avg_qual in variant_stats:
                print(f"     {chrom}: {count} variants (avg quality: {avg_qual:.2f})")
        
        # Gene expression data
        cur.execute("SELECT COUNT(*) FROM gene_expression")
        gene_count = cur.fetchone()[0]
        print(f"🔬 Gene Expression: {gene_count}")
        
        if gene_count > 0:
            cur.execute("""
                SELECT gene_name, AVG(CAST(expression_value AS FLOAT)) as avg_expression,
                       COUNT(*) as sample_count
                FROM gene_expression 
                GROUP BY gene_name 
                ORDER BY avg_expression DESC 
                LIMIT 5
            """)
            gene_stats = cur.fetchall()
            print("   Top genes by expression:")
            for gene, avg_expr, samples in gene_stats:
                print(f"     {gene}: {avg_expr:.2f} avg expression ({samples} samples)")
        
        # Drug targets data
        cur.execute("SELECT COUNT(*) FROM drug_targets")
        drug_count = cur.fetchone()[0]
        print(f"💊 Drug Targets: {drug_count}")
        
        if drug_count > 0:
            cur.execute("""
                SELECT drug_name, target_protein, binding_affinity
                FROM drug_targets 
                ORDER BY binding_affinity ASC 
                LIMIT 5
            """)
            drug_stats = cur.fetchall()
            print("   Top drugs by binding affinity:")
            for drug, target, affinity in drug_stats:
                print(f"     {drug} -> {target}: {affinity} nM")
        
        # Literature data
        cur.execute("SELECT COUNT(*) FROM literature_entities")
        lit_count = cur.fetchone()[0]
        print(f"📚 Literature Entities: {lit_count}")
        
        if lit_count > 0:
            cur.execute("""
                SELECT entity_type, COUNT(*) as count
                FROM literature_entities 
                GROUP BY entity_type 
                ORDER BY count DESC
            """)
            lit_stats = cur.fetchall()
            print("   Literature entity types:")
            for entity_type, count in lit_stats:
                print(f"     {entity_type}: {count}")
        
        # Samples data
        cur.execute("SELECT COUNT(*) FROM samples")
        sample_count = cur.fetchone()[0]
        print(f"🧪 Samples: {sample_count}")
        
        if sample_count > 0:
            cur.execute("""
                SELECT sample_type, COUNT(*) as count
                FROM samples 
                GROUP BY sample_type 
                ORDER BY count DESC
            """)
            sample_stats = cur.fetchall()
            print("   Sample types:")
            for sample_type, count in sample_stats:
                print(f"     {sample_type}: {count}")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("✅ Database analysis complete!")
        
        return {
            'variants': variant_count,
            'gene_expression': gene_count,
            'drug_targets': drug_count,
            'literature': lit_count,
            'samples': sample_count
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    check_database_data() 