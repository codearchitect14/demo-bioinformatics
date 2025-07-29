#!/usr/bin/env python3
"""
Master Pipeline Runner

This script runs all data pipelines for the genomics platform,
including ClinVar, TCGA, PubMed, 1000 Genomes, ENCODE, and ChEMBL.
"""

import asyncio
import os
import sys
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets.clinvar_pipeline import ClinVarPipeline
from datasets.tcga_pipeline import TCGAPipeline
from datasets.pubmed_pipeline import PubMedPipeline
from datasets.1000genomes_pipeline import ThousandGenomesPipeline
from datasets.encode_pipeline import ENCODEPipeline
from datasets.chembl_pipeline import ChEMBLPipeline
from utils.logging_utils import setup_logger


class MasterPipelineRunner:
    """Master pipeline runner for all genomics datasets."""
    
    def __init__(self):
        self.logger = setup_logger("master_pipeline_runner")
        self.pipelines = {
            "clinvar": ClinVarPipeline,
            "tcga": TCGAPipeline,
            "pubmed": PubMedPipeline,
            "1000genomes": ThousandGenomesPipeline,
            "encode": ENCODEPipeline,
            "chembl": ChEMBLPipeline
        }
        self.results = {}
        
    async def run_pipeline(self, pipeline_name: str, pipeline_class) -> Dict[str, Any]:
        """Run a single pipeline."""
        self.logger.info(f"Starting {pipeline_name} pipeline...")
        
        try:
            pipeline = pipeline_class()
            result = await pipeline.run()
            
            self.logger.info(f"{pipeline_name} pipeline completed successfully")
            return {
                "status": "success",
                "pipeline_name": pipeline_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"{pipeline_name} pipeline failed: {e}")
            return {
                "status": "failed",
                "pipeline_name": pipeline_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_all_pipelines(self) -> Dict[str, Any]:
        """Run all pipelines."""
        self.logger.info("Starting master pipeline runner...")
        
        start_time = datetime.now()
        
        # Run pipelines sequentially
        for pipeline_name, pipeline_class in self.pipelines.items():
            result = await self.run_pipeline(pipeline_name, pipeline_class)
            self.results[pipeline_name] = result
            
            # Small delay between pipelines
            await asyncio.sleep(1)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = self.generate_summary(duration)
        
        # Save results
        self.save_results(summary)
        
        return summary
    
    def generate_summary(self, duration: float) -> Dict[str, Any]:
        """Generate summary of all pipeline runs."""
        successful_pipelines = [name for name, result in self.results.items() 
                              if result["status"] == "success"]
        failed_pipelines = [name for name, result in self.results.items() 
                           if result["status"] == "failed"]
        
        summary = {
            "total_pipelines": len(self.pipelines),
            "successful_pipelines": len(successful_pipelines),
            "failed_pipelines": len(failed_pipelines),
            "success_rate": len(successful_pipelines) / len(self.pipelines),
            "duration_seconds": duration,
            "start_time": datetime.now().isoformat(),
            "pipeline_results": self.results,
            "successful_pipelines_list": successful_pipelines,
            "failed_pipelines_list": failed_pipelines
        }
        
        self.logger.info(f"Master pipeline completed: {len(successful_pipelines)}/{len(self.pipelines)} successful")
        return summary
    
    def save_results(self, summary: Dict[str, Any]):
        """Save results to file."""
        results_dir = Path("data") / "pipeline_results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"master_pipeline_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"Results saved to {results_file}")
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print a formatted summary."""
        print("\n" + "="*60)
        print("🧬 MASTER PIPELINE RUNNER SUMMARY")
        print("="*60)
        
        print(f"📊 Total Pipelines: {summary['total_pipelines']}")
        print(f"✅ Successful: {summary['successful_pipelines']}")
        print(f"❌ Failed: {summary['failed_pipelines']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1%}")
        print(f"⏱️  Duration: {summary['duration_seconds']:.1f} seconds")
        
        print(f"\n✅ Successful Pipelines:")
        for pipeline in summary['successful_pipelines_list']:
            print(f"   - {pipeline}")
        
        if summary['failed_pipelines_list']:
            print(f"\n❌ Failed Pipelines:")
            for pipeline in summary['failed_pipelines_list']:
                print(f"   - {pipeline}")
        
        print("\n" + "="*60)


async def main():
    """Main function."""
    runner = MasterPipelineRunner()
    
    try:
        summary = await runner.run_all_pipelines()
        runner.print_summary(summary)
        
        if summary['success_rate'] == 1.0:
            print("\n🎉 All pipelines completed successfully!")
        else:
            print(f"\n⚠️  {summary['failed_pipelines']} pipeline(s) failed. Check logs for details.")
            
    except Exception as e:
        print(f"❌ Master pipeline runner failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 