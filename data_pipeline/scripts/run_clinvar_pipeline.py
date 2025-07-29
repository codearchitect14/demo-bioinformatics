#!/usr/bin/env python3
"""
Script to run the ClinVar data pipeline.

This script downloads, validates, transforms, and loads ClinVar data
into the genomics platform database.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets.clinvar_pipeline import ClinVarPipeline
from utils.logging_utils import setup_logger


async def main():
    """Main function to run the ClinVar pipeline."""
    # Set up logging
    logger = setup_logger("clinvar_pipeline_runner")
    
    logger.info("Starting ClinVar pipeline execution")
    
    # Configuration for ClinVar pipeline
    config = {
        "data_path": os.getenv("CLINVAR_DATA_PATH", "/data/clinvar"),
        "batch_size": int(os.getenv("CLINVAR_BATCH_SIZE", "1000")),
        "max_retries": int(os.getenv("CLINVAR_MAX_RETRIES", "3")),
        "timeout": int(os.getenv("CLINVAR_TIMEOUT", "300")),
        "update_frequency": os.getenv("CLINVAR_UPDATE_FREQUENCY", "daily"),
        "indexes": [
            {"name": "idx_clinvar_variant_id", "columns": ["variant_id"]},
            {"name": "idx_clinvar_gene_id", "columns": ["gene_id"]},
            {"name": "idx_clinvar_chromosome_position", "columns": ["chromosome", "position"]},
            {"name": "idx_clinvar_clinical_significance", "columns": ["clinical_significance"]},
            {"name": "idx_clinvar_rs_id", "columns": ["rs_id"]}
        ]
    }
    
    try:
        # Initialize pipeline
        pipeline = ClinVarPipeline(config)
        
        # Run pipeline
        results = await pipeline.run()
        
        # Log results
        logger.info("ClinVar pipeline completed successfully")
        logger.info(f"Results: {json.dumps(results, indent=2)}")
        
        # Generate data summary
        summary = pipeline.get_data_summary()
        logger.info(f"Data summary: {json.dumps(summary, indent=2)}")
        
        # Save results to file
        results_file = Path(config["data_path"]) / "logs" / f"clinvar_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                "results": results,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")
        
        # Clean up
        pipeline.cleanup()
        
        return results
        
    except Exception as e:
        logger.error(f"ClinVar pipeline failed: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        print("ClinVar pipeline completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"ClinVar pipeline failed: {str(e)}")
        sys.exit(1) 