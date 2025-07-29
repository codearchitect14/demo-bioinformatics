"""
ClinVar data pipeline implementation.

This module provides a complete pipeline for downloading, processing, and
loading ClinVar data into the genomics platform.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import gzip
import shutil

from base.base_pipeline import BaseDatasetPipeline
from utils.download_utils import DownloadManager
from utils.logging_utils import setup_logger


class ClinVarPipeline(BaseDatasetPipeline):
    """
    Pipeline for processing ClinVar data.
    
    ClinVar is a freely accessible, public archive of reports of the relationships
    between human variations and phenotypes, with supporting evidence.
    """
    
    def __init__(self, config: Dict[str, Any], db_session=None, cache_enabled: bool = True):
        """
        Initialize ClinVar pipeline.
        
        Args:
            config: Pipeline configuration
            db_session: Database session
            cache_enabled: Whether to enable caching
        """
        super().__init__("clinvar", config, db_session, cache_enabled)
        
        # ClinVar-specific configuration
        self.clinvar_urls = {
            "variants": "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz",
            "submissions": "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/submission_summary.txt.gz",
            "traits": "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/trait_summary.txt.gz"
        }
        
        # Schema for ClinVar data
        self.variant_schema = {
            "required_columns": [
                "AlleleID", "Type", "Name", "GeneID", "GeneSymbol", "HGNC_ID",
                "ClinicalSignificance", "ClinSigSimple", "LastEvaluated", "RS# (dbSNP)",
                "nsv/esv (dbVar)", "PhenotypeIDs", "PhenotypeList", "Origin",
                "Assembly", "ChromosomeAccession", "Chromosome", "Start", "Stop",
                "ReferenceAllele", "AlternateAllele", "Cytogenetic", "ReviewStatus",
                "NumberSubmitters", "Guidelines", "TestedInGTR", "OtherIDs",
                "SubmitterCategories", "VariationID"
            ],
            "column_types": {
                "AlleleID": "integer",
                "GeneID": "integer",
                "Start": "integer",
                "Stop": "integer",
                "NumberSubmitters": "integer",
                "VariationID": "integer",
                "Chromosome": "string",
                "ClinicalSignificance": "string",
                "Type": "string"
            },
            "value_ranges": {
                "Start": {"min": 1},
                "Stop": {"min": 1},
                "NumberSubmitters": {"min": 0}
            }
        }
    
    async def _download_data(self) -> None:
        """Download ClinVar data files."""
        self.logger.info("Starting ClinVar data download")
        
        async with DownloadManager() as download_manager:
            download_tasks = []
            
            for data_type, url in self.clinvar_urls.items():
                destination = self.raw_data_path / f"{data_type}.txt.gz"
                
                # Check if file already exists and is recent
                if destination.exists():
                    file_age = datetime.now().timestamp() - destination.stat().st_mtime
                    if file_age < 24 * 3600:  # 24 hours
                        self.logger.info(f"Using existing {data_type} file")
                        continue
                
                self.logger.info(f"Downloading {data_type} from {url}")
                download_tasks.append(
                    download_manager.download_with_retry(
                        url=url,
                        destination=str(destination),
                        progress_callback=self._progress_callback
                    )
                )
            
            if download_tasks:
                results = await asyncio.gather(*download_tasks)
                
                for i, result in enumerate(results):
                    data_type = list(self.clinvar_urls.keys())[i]
                    if result["success"]:
                        self.logger.info(f"Successfully downloaded {data_type}")
                    else:
                        self.logger.error(f"Failed to download {data_type}: {result.get('error')}")
                        raise Exception(f"Download failed for {data_type}")
    
    async def _validate_data(self) -> None:
        """Validate downloaded ClinVar data."""
        self.logger.info("Validating ClinVar data")
        
        for data_type in self.clinvar_urls.keys():
            file_path = self.raw_data_path / f"{data_type}.txt.gz"
            
            if not file_path.exists():
                raise FileNotFoundError(f"Downloaded file not found: {file_path}")
            
            # Decompress and validate
            await self._validate_clinvar_file(file_path, data_type)
    
    async def _validate_clinvar_file(self, file_path: Path, data_type: str) -> None:
        """Validate a specific ClinVar file."""
        try:
            # Read first few lines to check format
            with gzip.open(file_path, 'rt') as f:
                header = f.readline().strip()
                sample_lines = [f.readline().strip() for _ in range(5)]
            
            # Validate header
            if data_type == "variants":
                expected_columns = self.variant_schema["required_columns"]
                actual_columns = header.split('\t')
                
                missing_columns = [col for col in expected_columns if col not in actual_columns]
                if missing_columns:
                    self.logger.warning(f"Missing columns in {data_type}: {missing_columns}")
                
                # Validate sample data
                for i, line in enumerate(sample_lines):
                    if line:
                        fields = line.split('\t')
                        if len(fields) < len(expected_columns):
                            self.logger.warning(f"Line {i+2} has fewer fields than expected")
            
            self.logger.info(f"Validation completed for {data_type}")
            
        except Exception as e:
            self.logger.error(f"Validation failed for {data_type}: {str(e)}")
            raise
    
    async def _transform_data(self) -> None:
        """Transform ClinVar data to unified schema."""
        self.logger.info("Transforming ClinVar data")
        
        # Process variants data (main focus)
        variants_file = self.raw_data_path / "variants.txt.gz"
        if variants_file.exists():
            await self._transform_variants_data(variants_file)
        
        # Process other data types if needed
        for data_type in ["submissions", "traits"]:
            file_path = self.raw_data_path / f"{data_type}.txt.gz"
            if file_path.exists():
                await self._transform_auxiliary_data(file_path, data_type)
    
    async def _transform_variants_data(self, file_path: Path) -> None:
        """Transform ClinVar variants data."""
        self.logger.info("Transforming variants data")
        
        # Read data in chunks to handle large files
        chunk_size = 10000
        chunk_number = 0
        
        for chunk in pd.read_csv(
            file_path,
            compression='gzip',
            sep='\t',
            chunksize=chunk_size,
            low_memory=False
        ):
            # Clean and transform chunk
            transformed_chunk = self._transform_variants_chunk(chunk)
            
            # Save transformed chunk
            output_file = self.processed_data_path / f"variants_chunk_{chunk_number:04d}.parquet"
            transformed_chunk.to_parquet(output_file, index=False)
            
            chunk_number += 1
            self.logger.info(f"Processed chunk {chunk_number}")
        
        self.logger.info(f"Transformed {chunk_number} chunks of variants data")
    
    def _transform_variants_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Transform a chunk of variants data."""
        # Apply column mapping
        column_mapping = {
            "AlleleID": "variant_id",
            "Type": "variant_type",
            "Name": "variant_name",
            "GeneID": "gene_id",
            "GeneSymbol": "gene_symbol",
            "HGNC_ID": "hgnc_id",
            "ClinicalSignificance": "clinical_significance",
            "ClinSigSimple": "clinical_significance_simple",
            "LastEvaluated": "last_evaluated",
            "RS# (dbSNP)": "rs_id",
            "nsv/esv (dbVar)": "dbvar_id",
            "PhenotypeIDs": "phenotype_ids",
            "PhenotypeList": "phenotype_list",
            "Origin": "origin",
            "Assembly": "assembly",
            "ChromosomeAccession": "chromosome_accession",
            "Chromosome": "chromosome",
            "Start": "position",
            "Stop": "end_position",
            "ReferenceAllele": "reference_allele",
            "AlternateAllele": "alternate_allele",
            "Cytogenetic": "cytogenetic",
            "ReviewStatus": "review_status",
            "NumberSubmitters": "number_submitters",
            "Guidelines": "guidelines",
            "TestedInGTR": "tested_in_gtr",
            "OtherIDs": "other_ids",
            "SubmitterCategories": "submitter_categories",
            "VariationID": "variation_id"
        }
        
        # Rename columns
        chunk = chunk.rename(columns=column_mapping)
        
        # Clean and standardize data
        chunk = self._clean_variants_data(chunk)
        
        # Add metadata
        chunk["source_type"] = "clinvar"
        chunk["transformed_at"] = datetime.now().isoformat()
        chunk["data_version"] = "1.0"
        
        return chunk
    
    def _clean_variants_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize variants data."""
        # Handle missing values
        data = data.replace(['', 'nan', 'None'], np.nan)
        
        # Convert data types
        numeric_columns = ["variant_id", "gene_id", "position", "end_position", "number_submitters", "variation_id"]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Standardize chromosome names
        if "chromosome" in data.columns:
            data["chromosome"] = data["chromosome"].astype(str).str.replace("chr", "")
        
        # Standardize clinical significance
        if "clinical_significance" in data.columns:
            data["clinical_significance"] = data["clinical_significance"].str.lower()
        
        # Parse phenotype IDs
        if "phenotype_ids" in data.columns:
            data["phenotype_ids"] = data["phenotype_ids"].str.split(";")
        
        # Clean allele sequences
        for col in ["reference_allele", "alternate_allele"]:
            if col in data.columns:
                data[col] = data[col].str.upper()
        
        return data
    
    async def _transform_auxiliary_data(self, file_path: Path, data_type: str) -> None:
        """Transform auxiliary ClinVar data (submissions, traits)."""
        self.logger.info(f"Transforming {data_type} data")
        
        # Read and transform auxiliary data
        data = pd.read_csv(file_path, compression='gzip', sep='\t', low_memory=False)
        
        # Apply basic transformations
        data = data.replace(['', 'nan', 'None'], np.nan)
        data["source_type"] = f"clinvar_{data_type}"
        data["transformed_at"] = datetime.now().isoformat()
        data["data_version"] = "1.0"
        
        # Save transformed data
        output_file = self.processed_data_path / f"{data_type}.parquet"
        data.to_parquet(output_file, index=False)
        
        self.logger.info(f"Transformed {len(data)} {data_type} records")
    
    async def _load_batch(self, batch: pd.DataFrame) -> None:
        """Load a batch of ClinVar data into database."""
        if not self.db_session:
            return
        
        try:
            # Convert DataFrame to list of dictionaries
            records = batch.to_dict('records')
            
            # Insert records into database
            # This would typically use SQLAlchemy models
            # For now, we'll just log the operation
            self.logger.debug(f"Loading batch of {len(records)} ClinVar records")
            
            # Example database insertion (commented out for now)
            # for record in records:
            #     variant = ClinVarVariant(**record)
            #     self.db_session.add(variant)
            # 
            # self.db_session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to load batch: {str(e)}")
            self.db_session.rollback()
            raise
    
    async def _create_index(self, index_config: Dict[str, Any]) -> None:
        """Create database indexes for ClinVar data."""
        if not self.db_session:
            return
        
        try:
            # Create indexes for efficient querying
            indexes = [
                {"name": "idx_clinvar_variant_id", "columns": ["variant_id"]},
                {"name": "idx_clinvar_gene_id", "columns": ["gene_id"]},
                {"name": "idx_clinvar_chromosome_position", "columns": ["chromosome", "position"]},
                {"name": "idx_clinvar_clinical_significance", "columns": ["clinical_significance"]},
                {"name": "idx_clinvar_rs_id", "columns": ["rs_id"]}
            ]
            
            for index in indexes:
                self.logger.debug(f"Creating index: {index['name']}")
                # This would typically execute SQL CREATE INDEX statements
                # For now, we'll just log the operation
            
        except Exception as e:
            self.logger.error(f"Failed to create indexes: {str(e)}")
            raise
    
    async def _prepare_cache_data(self) -> Optional[Dict[str, Any]]:
        """Prepare ClinVar data for caching."""
        try:
            # Cache frequently accessed data
            cache_data = {
                "clinical_significance_counts": {},
                "gene_variant_counts": {},
                "chromosome_variant_counts": {}
            }
            
            # Read processed data to generate cache
            processed_files = list(self.processed_data_path.glob("variants_chunk_*.parquet"))
            
            if processed_files:
                # Sample data for cache (first chunk)
                sample_data = pd.read_parquet(processed_files[0])
                
                # Generate cache statistics
                if "clinical_significance" in sample_data.columns:
                    cache_data["clinical_significance_counts"] = sample_data["clinical_significance"].value_counts().to_dict()
                
                if "gene_id" in sample_data.columns:
                    cache_data["gene_variant_counts"] = sample_data["gene_id"].value_counts().head(100).to_dict()
                
                if "chromosome" in sample_data.columns:
                    cache_data["chromosome_variant_counts"] = sample_data["chromosome"].value_counts().to_dict()
            
            return cache_data
            
        except Exception as e:
            self.logger.error(f"Failed to prepare cache data: {str(e)}")
            return None
    
    def _progress_callback(self, progress: float, downloaded: int, total: int) -> None:
        """Callback for download progress."""
        if int(progress) % 10 == 0:
            self.logger.info(f"Download progress: {progress:.1f}% ({downloaded}/{total} bytes)")
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of ClinVar data."""
        summary = {
            "dataset_name": "clinvar",
            "total_variants": 0,
            "clinical_significance_distribution": {},
            "gene_distribution": {},
            "chromosome_distribution": {}
        }
        
        try:
            # Count total variants
            processed_files = list(self.processed_data_path.glob("variants_chunk_*.parquet"))
            for file_path in processed_files:
                data = pd.read_parquet(file_path)
                summary["total_variants"] += len(data)
                
                # Update distributions
                if "clinical_significance" in data.columns:
                    counts = data["clinical_significance"].value_counts()
                    for key, value in counts.items():
                        summary["clinical_significance_distribution"][key] = summary["clinical_significance_distribution"].get(key, 0) + value
                
                if "gene_id" in data.columns:
                    counts = data["gene_id"].value_counts()
                    for key, value in counts.items():
                        summary["gene_distribution"][key] = summary["gene_distribution"].get(key, 0) + value
                
                if "chromosome" in data.columns:
                    counts = data["chromosome"].value_counts()
                    for key, value in counts.items():
                        summary["chromosome_distribution"][key] = summary["chromosome_distribution"].get(key, 0) + value
            
            # Keep only top genes
            summary["gene_distribution"] = dict(sorted(summary["gene_distribution"].items(), key=lambda x: x[1], reverse=True)[:100])
            
        except Exception as e:
            self.logger.error(f"Failed to generate data summary: {str(e)}")
        
        return summary 