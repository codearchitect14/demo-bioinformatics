#!/usr/bin/env python3
"""
Script to run the PubMed data pipeline.

This script downloads, validates, transforms, and loads PubMed data
into the genomics platform database for literature mining.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets.pubmed_pipeline import PubMedPipeline
from utils.logging_utils import setup_logger


async def main():
    """Main function to run the PubMed pipeline."""
    # Set up logging
    logger = setup_logger("pubmed_pipeline_runner")
    
    logger.info("Starting PubMed pipeline execution")
    
    # Configuration for PubMed pipeline
    config = {
        "data_path": os.getenv("PUBMED_DATA_PATH", "/data/pubmed"),
        "batch_size": int(os.getenv("PUBMED_BATCH_SIZE", "50")),
        "max_retries": int(os.getenv("PUBMED_MAX_RETRIES", "3")),
        "timeout": int(os.getenv("PUBMED_TIMEOUT", "300")),
        "update_frequency": os.getenv("PUBMED_UPDATE_FREQUENCY", "daily"),
        "pubmed_api_key": os.getenv("PUBMED_API_KEY", ""),
        "max_articles_per_request": int(os.getenv("PUBMED_MAX_ARTICLES", "100")),
        "delay_between_requests": float(os.getenv("PUBMED_DELAY", "0.34")),
        "search_terms": os.getenv("PUBMED_SEARCH_TERMS", "genomics,bioinformatics,genetic variation,gene expression,cancer genomics,precision medicine,drug discovery,biomarker,pharmacogenomics,genetic testing").split(","),
        "start_date": os.getenv("PUBMED_START_DATE", "2020-01-01"),
        "end_date": os.getenv("PUBMED_END_DATE", datetime.now().strftime("%Y-%m-%d")),
        "indexes": [
            {"name": "idx_pubmed_pmid", "columns": ["pmid"]},
            {"name": "idx_pubmed_search_term", "columns": ["search_term"]},
            {"name": "idx_pubmed_data_type", "columns": ["data_type"]},
            {"name": "idx_pubmed_publication_date", "columns": ["publication_date"]},
            {"name": "idx_pubmed_citing_pmid", "columns": ["citing_pmid"]},
            {"name": "idx_pubmed_cited_pmid", "columns": ["cited_pmid"]}
        ]
    }
    
    try:
        # Initialize pipeline
        pipeline = PubMedPipeline(config)
        
        # Run pipeline
        results = await pipeline.run()
        
        # Log results
        logger.info("PubMed pipeline completed successfully")
        logger.info(f"Results: {json.dumps(results, indent=2)}")
        
        # Generate data summary
        summary = pipeline.get_data_summary()
        logger.info(f"Data summary: {json.dumps(summary, indent=2)}")
        
        # Save results to file
        results_file = Path(config["data_path"]) / "logs" / f"pubmed_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
        logger.error(f"PubMed pipeline failed: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        print("PubMed pipeline completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"PubMed pipeline failed: {str(e)}")
        sys.exit(1) 