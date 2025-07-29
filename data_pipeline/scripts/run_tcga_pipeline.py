#!/usr/bin/env python3
"""
Script to run the TCGA data pipeline.

This script downloads, validates, transforms, and loads TCGA data
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

from datasets.tcga_pipeline import TCGAPipeline
from utils.logging_utils import setup_logger


async def main():
    """Main function to run the TCGA pipeline."""
    # Set up logging
    logger = setup_logger("tcga_pipeline_runner")
    
    logger.info("Starting TCGA pipeline execution")
    
    # Configuration for TCGA pipeline
    config = {
        "data_path": os.getenv("TCGA_DATA_PATH", "/data/tcga"),
        "batch_size": int(os.getenv("TCGA_BATCH_SIZE", "100")),
        "max_retries": int(os.getenv("TCGA_MAX_RETRIES", "3")),
        "timeout": int(os.getenv("TCGA_TIMEOUT", "600")),
        "update_frequency": os.getenv("TCGA_UPDATE_FREQUENCY", "weekly"),
        "cancer_types": os.getenv("TCGA_CANCER_TYPES", "BRCA,LUAD,LUSC,COAD,READ,STAD,LIHC,KIRC,KIRP,THCA").split(","),
        "indexes": [
            {"name": "idx_tcga_patient_id", "columns": ["patient_id"]},
            {"name": "idx_tcga_cancer_type", "columns": ["cancer_type"]},
            {"name": "idx_tcga_data_type", "columns": ["data_type"]},
            {"name": "idx_tcga_gene_id", "columns": ["gene_id"]},
            {"name": "idx_tcga_chromosome_position", "columns": ["chromosome", "position"]}
        ]
    }
    
    try:
        # Initialize pipeline
        pipeline = TCGAPipeline(config)
        
        # Run pipeline
        results = await pipeline.run()
        
        # Log results
        logger.info("TCGA pipeline completed successfully")
        logger.info(f"Results: {json.dumps(results, indent=2)}")
        
        # Generate data summary
        summary = pipeline.get_data_summary()
        logger.info(f"Data summary: {json.dumps(summary, indent=2)}")
        
        # Save results to file
        results_file = Path(config["data_path"]) / "logs" / f"tcga_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
        logger.error(f"TCGA pipeline failed: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        print("TCGA pipeline completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"TCGA pipeline failed: {str(e)}")
        sys.exit(1) 