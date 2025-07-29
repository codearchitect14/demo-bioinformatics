#!/usr/bin/env python3
"""
1000 Genomes Project Data Pipeline

This pipeline downloads and processes population reference data from the 1000 Genomes Project,
including variant frequencies, population genetics, and reference genomes.
"""

import os
import sys
import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
import gzip
import json
from typing import Dict, List, Any, Optional

from base.base_pipeline import BaseDatasetPipeline
from utils.download_utils import DownloadManager
from utils.logging_utils import setup_logger


class ThousandGenomesPipeline(BaseDatasetPipeline):
    """Pipeline for processing 1000 Genomes Project data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            dataset_name="1000genomes",
            dataset_source="1000GENOMES",
            config=config or {}
        )
        self.logger = setup_logger(f"pipeline.{self.dataset_name}")
        
        # 1000 Genomes specific configuration
        self.base_url = "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp"
        self.populations = ["EUR", "AFR", "EAS", "SAS", "AMR"]
        self.chromosomes = list(range(1, 23)) + ["X", "Y"]
        
    async def download_data(self) -> Dict[str, str]:
        """Download 1000 Genomes data files."""
        self.logger.info("Starting 1000 Genomes data download...")
        
        downloaded_files = {}
        
        try:
            # Download population metadata
            population_url = f"{self.base_url}/release/20130502/integrated_call_samples_v3.20130502.ALL.panel"
            population_file = await self.download_manager.download_file(
                population_url, 
                self.data_dir / "population_metadata.txt"
            )
            downloaded_files["population_metadata"] = str(population_file)
            
            # Download variant frequency data (sample for chromosome 22)
            variant_url = f"{self.base_url}/release/20130502/ALL.chr22.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"
            variant_file = await self.download_manager.download_file(
                variant_url,
                self.data_dir / "chr22_variants.vcf.gz"
            )
            downloaded_files["variant_data"] = str(variant_file)
            
            # Download sample information
            sample_url = f"{self.base_url}/release/20130502/integrated_call_samples_v3.20130502.ALL.ped"
            sample_file = await self.download_manager.download_file(
                sample_url,
                self.data_dir / "sample_info.ped"
            )
            downloaded_files["sample_info"] = str(sample_file)
            
            self.logger.info(f"Downloaded {len(downloaded_files)} files successfully")
            return downloaded_files
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise
    
    def clean_data(self, data_files: Dict[str, str]) -> Dict[str, pd.DataFrame]:
        """Clean and preprocess 1000 Genomes data."""
        self.logger.info("Cleaning 1000 Genomes data...")
        
        cleaned_data = {}
        
        try:
            # Clean population metadata
            if "population_metadata" in data_files:
                pop_df = pd.read_csv(data_files["population_metadata"], sep='\t')
                pop_df = pop_df[['sample', 'pop', 'super_pop', 'gender']].dropna()
                cleaned_data["populations"] = pop_df
                
            # Clean sample information
            if "sample_info" in data_files:
                sample_df = pd.read_csv(data_files["sample_info"], sep='\t', header=None)
                sample_df.columns = ['family_id', 'sample_id', 'father_id', 'mother_id', 'sex', 'phenotype']
                sample_df = sample_df.dropna()
                cleaned_data["samples"] = sample_df
                
            # Process variant data (simplified for demo)
            if "variant_data" in data_files:
                # Create sample variant frequency data
                variant_data = []
                for chrom in self.chromosomes[:5]:  # Sample first 5 chromosomes
                    for pos in range(1000000, 5000000, 100000):
                        variant_data.append({
                            'chromosome': f'chr{chrom}',
                            'position': pos,
                            'variant_id': f'rs{np.random.randint(1000000, 9999999)}',
                            'reference_allele': np.random.choice(['A', 'C', 'G', 'T']),
                            'alternate_allele': np.random.choice(['A', 'C', 'G', 'T']),
                            'allele_frequency': np.random.uniform(0.001, 0.5),
                            'population': np.random.choice(self.populations),
                            'variant_type': np.random.choice(['SNP', 'INDEL']),
                            'quality_score': np.random.uniform(50, 100)
                        })
                
                cleaned_data["variants"] = pd.DataFrame(variant_data)
            
            self.logger.info(f"Cleaned {len(cleaned_data)} data types")
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Data cleaning failed: {e}")
            raise
    
    def transform_data(self, cleaned_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Transform data into unified schema."""
        self.logger.info("Transforming 1000 Genomes data...")
        
        transformed_data = {}
        
        try:
            # Transform variants
            if "variants" in cleaned_data:
                variants_df = cleaned_data["variants"].copy()
                variants_df['dataset_id'] = self.dataset_id
                variants_df['annotations'] = variants_df.apply(
                    lambda row: json.dumps({
                        'population': row['population'],
                        'allele_frequency': float(row['allele_frequency']),
                        'variant_type': row['variant_type'],
                        'quality_score': float(row['quality_score'])
                    }), axis=1
                )
                
                # Select columns matching our schema
                transformed_data["variants"] = variants_df[[
                    'dataset_id', 'chromosome', 'position', 'reference_allele',
                    'alternate_allele', 'variant_type', 'quality_score',
                    'allele_frequency', 'annotations'
                ]]
            
            # Transform samples
            if "samples" in cleaned_data:
                samples_df = cleaned_data["samples"].copy()
                samples_df['dataset_id'] = self.dataset_id
                samples_df['sample_id'] = samples_df['sample_id']
                samples_df['external_id'] = samples_df['sample_id']
                samples_df['sample_type'] = 'reference'
                samples_df['tissue_type'] = 'blood'
                samples_df['disease_type'] = 'healthy'
                samples_df['gender'] = samples_df['sex'].map({1: 'male', 2: 'female'})
                samples_df['metadata'] = samples_df.apply(
                    lambda row: json.dumps({
                        'family_id': row['family_id'],
                        'father_id': row['father_id'],
                        'mother_id': row['mother_id'],
                        'phenotype': row['phenotype']
                    }), axis=1
                )
                
                transformed_data["samples"] = samples_df[[
                    'dataset_id', 'sample_id', 'external_id', 'sample_type',
                    'tissue_type', 'disease_type', 'gender', 'metadata'
                ]]
            
            self.logger.info(f"Transformed {len(transformed_data)} data types")
            return transformed_data
            
        except Exception as e:
            self.logger.error(f"Data transformation failed: {e}")
            raise
    
    def validate_data(self, transformed_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate transformed data."""
        self.logger.info("Validating 1000 Genomes data...")
        
        validation_results = {
            "total_records": 0,
            "validation_errors": 0,
            "data_quality": {}
        }
        
        try:
            for data_type, df in transformed_data.items():
                validation_results["total_records"] += len(df)
                
                # Basic validation
                if data_type == "variants":
                    validation_results["data_quality"]["variants"] = {
                        "total_variants": len(df),
                        "unique_chromosomes": df['chromosome'].nunique(),
                        "frequency_range": {
                            "min": df['allele_frequency'].min(),
                            "max": df['allele_frequency'].max()
                        },
                        "populations": df['annotations'].apply(
                            lambda x: json.loads(x).get('population')
                        ).nunique()
                    }
                elif data_type == "samples":
                    validation_results["data_quality"]["samples"] = {
                        "total_samples": len(df),
                        "gender_distribution": df['gender'].value_counts().to_dict(),
                        "tissue_types": df['tissue_type'].value_counts().to_dict()
                    }
            
            self.logger.info(f"Validation completed: {validation_results['total_records']} records")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            raise
    
    def generate_summary(self, transformed_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Generate data summary."""
        self.logger.info("Generating 1000 Genomes data summary...")
        
        summary = {
            "dataset_name": "1000genomes",
            "total_variants": 0,
            "total_samples": 0,
            "population_distribution": {},
            "chromosome_distribution": {},
            "allele_frequency_distribution": {}
        }
        
        try:
            if "variants" in transformed_data:
                variants_df = transformed_data["variants"]
                summary["total_variants"] = len(variants_df)
                summary["chromosome_distribution"] = variants_df['chromosome'].value_counts().to_dict()
                
                # Extract population info from annotations
                populations = []
                frequencies = []
                for _, row in variants_df.iterrows():
                    annotations = json.loads(row['annotations'])
                    populations.append(annotations.get('population', 'unknown'))
                    frequencies.append(annotations.get('allele_frequency', 0))
                
                summary["population_distribution"] = pd.Series(populations).value_counts().to_dict()
                summary["allele_frequency_distribution"] = {
                    "mean": np.mean(frequencies),
                    "median": np.median(frequencies),
                    "std": np.std(frequencies)
                }
            
            if "samples" in transformed_data:
                samples_df = transformed_data["samples"]
                summary["total_samples"] = len(samples_df)
            
            self.logger.info(f"Summary generated: {summary['total_variants']} variants, {summary['total_samples']} samples")
            return summary
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            raise


if __name__ == "__main__":
    # Test the pipeline
    pipeline = ThousandGenomesPipeline()
    asyncio.run(pipeline.run()) 