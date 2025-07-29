"""
TCGA (The Cancer Genome Atlas) data pipeline implementation.

This module provides a complete pipeline for downloading, processing, and
loading TCGA data into the genomics platform.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import gzip
import shutil
import requests
from urllib.parse import urljoin

from base.base_pipeline import BaseDatasetPipeline
from utils.download_utils import DownloadManager
from utils.logging_utils import setup_logger


class TCGAPipeline(BaseDatasetPipeline):
    """
    Pipeline for processing TCGA (The Cancer Genome Atlas) data.
    
    TCGA is a comprehensive cancer genomics dataset containing gene expression,
    mutations, clinical data, and other omics data for various cancer types.
    """
    
    def __init__(self, config: Dict[str, Any], db_session=None, cache_enabled: bool = True):
        """
        Initialize TCGA pipeline.
        
        Args:
            config: Pipeline configuration
            db_session: Database session
            cache_enabled: Whether to enable caching
        """
        super().__init__("tcga", config, db_session, cache_enabled)
        
        # TCGA-specific configuration
        self.gdc_api_base = "https://api.gdc.cancer.gov"
        self.tcga_data_types = {
            "clinical": "clinical",
            "gene_expression": "gene_expression",
            "mutations": "mutations",
            "copy_number": "copy_number_variation",
            "methylation": "methylation_beta_value",
            "protein_expression": "protein_expression"
        }
        
        # Cancer types to process
        self.cancer_types = config.get("cancer_types", [
            "BRCA", "LUAD", "LUSC", "COAD", "READ", "STAD", "LIHC", "KIRC", "KIRP", "THCA"
        ])
        
        # Schema definitions for different data types
        self.schemas = {
            "clinical": {
                "required_columns": [
                    "submitter_id", "project_id", "age_at_index", "gender", "race", "ethnicity",
                    "vital_status", "days_to_death", "days_to_last_follow_up", "tumor_stage",
                    "tumor_grade", "primary_diagnosis", "tumor_type"
                ],
                "column_types": {
                    "age_at_index": "integer",
                    "days_to_death": "integer",
                    "days_to_last_follow_up": "integer"
                }
            },
            "gene_expression": {
                "required_columns": [
                    "gene_id", "gene_name", "sample_id", "expression_value", "expression_unit"
                ],
                "column_types": {
                    "expression_value": "float"
                }
            },
            "mutations": {
                "required_columns": [
                    "chromosome", "position", "reference_allele", "alternate_allele",
                    "variant_type", "gene_id", "gene_name", "sample_id", "mutation_type"
                ],
                "column_types": {
                    "position": "integer"
                }
            }
        }
    
    async def _download_data(self) -> None:
        """Download TCGA data from GDC API."""
        self.logger.info("Starting TCGA data download")
        
        # Create download tasks for each cancer type and data type
        download_tasks = []
        
        for cancer_type in self.cancer_types:
            for data_type, gdc_type in self.tcga_data_types.items():
                task = self._download_cancer_data(cancer_type, data_type, gdc_type)
                download_tasks.append(task)
        
        # Execute downloads concurrently
        if download_tasks:
            results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Download task {i} failed: {str(result)}")
                elif not result.get("success", False):
                    self.logger.error(f"Download task {i} failed: {result.get('error')}")
                else:
                    self.logger.info(f"Download task {i} completed successfully")
    
    async def _download_cancer_data(self, cancer_type: str, data_type: str, gdc_type: str) -> Dict[str, Any]:
        """Download data for a specific cancer type and data type."""
        try:
            self.logger.info(f"Downloading {cancer_type} {data_type} data")
            
            # Query GDC API for available files
            files = await self._query_gdc_files(cancer_type, gdc_type)
            
            if not files:
                self.logger.warning(f"No files found for {cancer_type} {data_type}")
                return {"success": True, "message": "No files to download"}
            
            # Download files
            download_results = []
            async with DownloadManager() as download_manager:
                for file_info in files[:10]:  # Limit to first 10 files for testing
                    file_id = file_info["file_id"]
                    file_name = file_info["file_name"]
                    
                    # Create destination path
                    dest_path = self.raw_data_path / cancer_type / data_type / file_name
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Download file
                    result = await download_manager.download_with_retry(
                        url=f"{self.gdc_api_base}/data/{file_id}",
                        destination=str(dest_path),
                        progress_callback=self._progress_callback
                    )
                    
                    download_results.append(result)
            
            # Check results
            successful_downloads = sum(1 for r in download_results if r.get("success", False))
            total_downloads = len(download_results)
            
            self.logger.info(f"Downloaded {successful_downloads}/{total_downloads} files for {cancer_type} {data_type}")
            
            return {
                "success": successful_downloads > 0,
                "cancer_type": cancer_type,
                "data_type": data_type,
                "successful_downloads": successful_downloads,
                "total_downloads": total_downloads
            }
            
        except Exception as e:
            self.logger.error(f"Failed to download {cancer_type} {data_type}: {str(e)}")
            return {
                "success": False,
                "cancer_type": cancer_type,
                "data_type": data_type,
                "error": str(e)
            }
    
    async def _query_gdc_files(self, cancer_type: str, data_type: str) -> List[Dict[str, Any]]:
        """Query GDC API for available files."""
        try:
            # Build query
            query = {
                "filters": {
                    "op": "and",
                    "content": [
                        {
                            "op": "=",
                            "content": {
                                "field": "cases.project.project_id",
                                "value": f"TCGA-{cancer_type}"
                            }
                        },
                        {
                            "op": "=",
                            "content": {
                                "field": "files.data_type",
                                "value": data_type
                            }
                        }
                    ]
                },
                "fields": ["file_id", "file_name", "file_size", "data_type", "data_format"],
                "size": 100
            }
            
            # Make API request
            async with DownloadManager() as download_manager:
                if hasattr(download_manager, 'session') and download_manager.session:
                    async with download_manager.session.post(
                        f"{self.gdc_api_base}/files",
                        json=query,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get("data", {}).get("hits", [])
                        else:
                            self.logger.error(f"GDC API query failed: {response.status}")
                            return []
                else:
                    # Fallback to synchronous request
                    response = requests.post(
                        f"{self.gdc_api_base}/files",
                        json=query,
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return data.get("data", {}).get("hits", [])
                    else:
                        self.logger.error(f"GDC API query failed: {response.status_code}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Failed to query GDC API: {str(e)}")
            return []
    
    async def _validate_data(self) -> None:
        """Validate downloaded TCGA data."""
        self.logger.info("Validating TCGA data")
        
        for cancer_type in self.cancer_types:
            for data_type in self.tcga_data_types.keys():
                data_dir = self.raw_data_path / cancer_type / data_type
                
                if data_dir.exists():
                    await self._validate_cancer_data(cancer_type, data_type, data_dir)
    
    async def _validate_cancer_data(self, cancer_type: str, data_type: str, data_dir: Path) -> None:
        """Validate data for a specific cancer type and data type."""
        try:
            files = list(data_dir.glob("*"))
            
            if not files:
                self.logger.warning(f"No files found in {data_dir}")
                return
            
            # Validate first few files
            for file_path in files[:5]:  # Validate first 5 files
                await self._validate_tcga_file(file_path, data_type)
            
            self.logger.info(f"Validation completed for {cancer_type} {data_type}")
            
        except Exception as e:
            self.logger.error(f"Validation failed for {cancer_type} {data_type}: {str(e)}")
            raise
    
    async def _validate_tcga_file(self, file_path: Path, data_type: str) -> None:
        """Validate a specific TCGA file."""
        try:
            # Check file size
            if file_path.stat().st_size == 0:
                raise ValueError(f"Empty file: {file_path}")
            
            # Check file format based on data type
            if data_type == "clinical":
                # Clinical data is typically JSON or TSV
                if file_path.suffix in ['.json', '.tsv', '.txt']:
                    # Basic format validation
                    with open(file_path, 'r') as f:
                        first_line = f.readline().strip()
                        if not first_line:
                            raise ValueError(f"Empty first line in {file_path}")
            
            elif data_type == "gene_expression":
                # Gene expression data is typically TSV or CSV
                if file_path.suffix in ['.tsv', '.txt', '.csv']:
                    # Check if file has expected columns
                    df = pd.read_csv(file_path, sep='\t' if file_path.suffix == '.tsv' else ',', nrows=5)
                    expected_columns = ["gene_id", "gene_name", "expression_value"]
                    missing_columns = [col for col in expected_columns if col not in df.columns]
                    if missing_columns:
                        self.logger.warning(f"Missing expected columns in {file_path}: {missing_columns}")
            
            elif data_type == "mutations":
                # Mutation data is typically VCF or MAF format
                if file_path.suffix in ['.vcf', '.maf', '.txt']:
                    # Basic format validation
                    with open(file_path, 'r') as f:
                        first_line = f.readline().strip()
                        if not first_line.startswith('#') and data_type == "mutations":
                            self.logger.warning(f"Mutation file {file_path} may not be in expected format")
            
        except Exception as e:
            self.logger.error(f"File validation failed for {file_path}: {str(e)}")
            raise
    
    async def _transform_data(self) -> None:
        """Transform TCGA data to unified schema."""
        self.logger.info("Transforming TCGA data")
        
        for cancer_type in self.cancer_types:
            for data_type in self.tcga_data_types.keys():
                data_dir = self.raw_data_path / cancer_type / data_type
                
                if data_dir.exists():
                    await self._transform_cancer_data(cancer_type, data_type, data_dir)
    
    async def _transform_cancer_data(self, cancer_type: str, data_type: str, data_dir: Path) -> None:
        """Transform data for a specific cancer type and data type."""
        try:
            files = list(data_dir.glob("*"))
            
            if not files:
                return
            
            # Process files
            for file_path in files:
                await self._transform_tcga_file(file_path, cancer_type, data_type)
            
            self.logger.info(f"Transformation completed for {cancer_type} {data_type}")
            
        except Exception as e:
            self.logger.error(f"Transformation failed for {cancer_type} {data_type}: {str(e)}")
            raise
    
    async def _transform_tcga_file(self, file_path: Path, cancer_type: str, data_type: str) -> None:
        """Transform a specific TCGA file."""
        try:
            # Read file based on format
            if file_path.suffix == '.json':
                data = self._read_json_file(file_path)
            elif file_path.suffix in ['.tsv', '.txt']:
                data = self._read_tsv_file(file_path)
            elif file_path.suffix == '.csv':
                data = pd.read_csv(file_path)
            else:
                self.logger.warning(f"Unsupported file format: {file_path.suffix}")
                return
            
            if data is None or len(data) == 0:
                self.logger.warning(f"Empty data in {file_path}")
                return
            
            # Transform data based on type
            if data_type == "clinical":
                transformed_data = self._transform_clinical_data(data, cancer_type)
            elif data_type == "gene_expression":
                transformed_data = self._transform_expression_data(data, cancer_type)
            elif data_type == "mutations":
                transformed_data = self._transform_mutation_data(data, cancer_type)
            else:
                transformed_data = self._transform_generic_data(data, cancer_type, data_type)
            
            # Save transformed data
            output_file = self.processed_data_path / cancer_type / data_type / f"{file_path.stem}_transformed.parquet"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            transformed_data.to_parquet(output_file, index=False)
            
            self.logger.debug(f"Transformed {file_path} -> {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to transform {file_path}: {str(e)}")
            raise
    
    def _read_json_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read JSON file and convert to DataFrame."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                # Flatten nested structure
                flattened_data = self._flatten_json(data)
                return pd.DataFrame([flattened_data])
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to read JSON file {file_path}: {str(e)}")
            return None
    
    def _read_tsv_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read TSV file and convert to DataFrame."""
        try:
            # Try different separators
            for sep in ['\t', ',', '|']:
                try:
                    data = pd.read_csv(file_path, sep=sep, low_memory=False)
                    if len(data.columns) > 1:  # Likely correct separator
                        return data
                except:
                    continue
            
            # If all separators fail, try with default
            return pd.read_csv(file_path, low_memory=False)
            
        except Exception as e:
            self.logger.error(f"Failed to read TSV file {file_path}: {str(e)}")
            return None
    
    def _flatten_json(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested JSON structure."""
        flattened = {}
        
        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self._flatten_json(value, new_key))
            elif isinstance(value, list):
                flattened[new_key] = json.dumps(value)
            else:
                flattened[new_key] = value
        
        return flattened
    
    def _transform_clinical_data(self, data: pd.DataFrame, cancer_type: str) -> pd.DataFrame:
        """Transform clinical data."""
        # Standardize column names
        column_mapping = {
            "submitter_id": "patient_id",
            "project_id": "project_id",
            "age_at_index": "age",
            "gender": "gender",
            "race": "race",
            "ethnicity": "ethnicity",
            "vital_status": "vital_status",
            "days_to_death": "days_to_death",
            "days_to_last_follow_up": "days_to_last_followup",
            "tumor_stage": "tumor_stage",
            "tumor_grade": "tumor_grade",
            "primary_diagnosis": "primary_diagnosis",
            "tumor_type": "tumor_type"
        }
        
        # Rename columns
        data = data.rename(columns=column_mapping)
        
        # Add metadata
        data["cancer_type"] = cancer_type
        data["data_type"] = "clinical"
        data["source_type"] = "tcga"
        data["transformed_at"] = datetime.now().isoformat()
        data["data_version"] = "1.0"
        
        # Clean data
        data = self._clean_clinical_data(data)
        
        return data
    
    def _transform_expression_data(self, data: pd.DataFrame, cancer_type: str) -> pd.DataFrame:
        """Transform gene expression data."""
        # Handle different expression data formats
        if "gene_id" in data.columns and "expression_value" in data.columns:
            # Already in expected format
            pass
        elif "gene" in data.columns and "expression" in data.columns:
            # Rename columns
            data = data.rename(columns={
                "gene": "gene_id",
                "expression": "expression_value"
            })
        else:
            # Try to identify gene and expression columns
            gene_cols = [col for col in data.columns if "gene" in col.lower()]
            expr_cols = [col for col in data.columns if any(term in col.lower() for term in ["expression", "count", "tpm", "fpkm"])]
            
            if gene_cols and expr_cols:
                data = data.rename(columns={
                    gene_cols[0]: "gene_id",
                    expr_cols[0]: "expression_value"
                })
        
        # Add metadata
        data["cancer_type"] = cancer_type
        data["data_type"] = "gene_expression"
        data["source_type"] = "tcga"
        data["transformed_at"] = datetime.now().isoformat()
        data["data_version"] = "1.0"
        
        # Clean data
        data = self._clean_expression_data(data)
        
        return data
    
    def _transform_mutation_data(self, data: pd.DataFrame, cancer_type: str) -> pd.DataFrame:
        """Transform mutation data."""
        # Handle different mutation data formats
        if "chromosome" in data.columns and "position" in data.columns:
            # Already in expected format
            pass
        else:
            # Try to identify genomic columns
            chr_cols = [col for col in data.columns if "chr" in col.lower()]
            pos_cols = [col for col in data.columns if "pos" in col.lower() or "start" in col.lower()]
            
            if chr_cols and pos_cols:
                data = data.rename(columns={
                    chr_cols[0]: "chromosome",
                    pos_cols[0]: "position"
                })
        
        # Add metadata
        data["cancer_type"] = cancer_type
        data["data_type"] = "mutations"
        data["source_type"] = "tcga"
        data["transformed_at"] = datetime.now().isoformat()
        data["data_version"] = "1.0"
        
        # Clean data
        data = self._clean_mutation_data(data)
        
        return data
    
    def _transform_generic_data(self, data: pd.DataFrame, cancer_type: str, data_type: str) -> pd.DataFrame:
        """Transform generic data."""
        # Add metadata
        data["cancer_type"] = cancer_type
        data["data_type"] = data_type
        data["source_type"] = "tcga"
        data["transformed_at"] = datetime.now().isoformat()
        data["data_version"] = "1.0"
        
        return data
    
    def _clean_clinical_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean clinical data."""
        # Handle missing values
        data = data.replace(['', 'nan', 'None', 'Unknown'], np.nan)
        
        # Convert data types
        numeric_columns = ["age", "days_to_death", "days_to_last_followup"]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Standardize categorical values
        if "gender" in data.columns:
            data["gender"] = data["gender"].str.upper()
        
        if "vital_status" in data.columns:
            data["vital_status"] = data["vital_status"].str.upper()
        
        return data
    
    def _clean_expression_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean expression data."""
        # Handle missing values
        data = data.replace(['', 'nan', 'None'], np.nan)
        
        # Convert expression values to numeric
        if "expression_value" in data.columns:
            data["expression_value"] = pd.to_numeric(data["expression_value"], errors='coerce')
        
        # Remove rows with missing expression values
        data = data.dropna(subset=["expression_value"])
        
        return data
    
    def _clean_mutation_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean mutation data."""
        # Handle missing values
        data = data.replace(['', 'nan', 'None'], np.nan)
        
        # Convert position to numeric
        if "position" in data.columns:
            data["position"] = pd.to_numeric(data["position"], errors='coerce')
        
        # Standardize chromosome names
        if "chromosome" in data.columns:
            data["chromosome"] = data["chromosome"].astype(str).str.replace("chr", "")
        
        # Clean allele sequences
        for col in ["reference_allele", "alternate_allele"]:
            if col in data.columns:
                data[col] = data[col].str.upper()
        
        return data
    
    async def _load_batch(self, batch: pd.DataFrame) -> None:
        """Load a batch of TCGA data into database."""
        if not self.db_session:
            return
        
        try:
            # Convert DataFrame to list of dictionaries
            records = batch.to_dict('records')
            
            # Insert records into database
            # This would typically use SQLAlchemy models
            # For now, we'll just log the operation
            self.logger.debug(f"Loading batch of {len(records)} TCGA records")
            
            # Example database insertion (commented out for now)
            # for record in records:
            #     tcga_record = TCGARecord(**record)
            #     self.db_session.add(tcga_record)
            # 
            # self.db_session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to load batch: {str(e)}")
            self.db_session.rollback()
            raise
    
    async def _create_index(self, index_config: Dict[str, Any]) -> None:
        """Create database indexes for TCGA data."""
        if not self.db_session:
            return
        
        try:
            # Create indexes for efficient querying
            indexes = [
                {"name": "idx_tcga_patient_id", "columns": ["patient_id"]},
                {"name": "idx_tcga_cancer_type", "columns": ["cancer_type"]},
                {"name": "idx_tcga_data_type", "columns": ["data_type"]},
                {"name": "idx_tcga_gene_id", "columns": ["gene_id"]},
                {"name": "idx_tcga_chromosome_position", "columns": ["chromosome", "position"]}
            ]
            
            for index in indexes:
                self.logger.debug(f"Creating index: {index['name']}")
                # This would typically execute SQL CREATE INDEX statements
                # For now, we'll just log the operation
            
        except Exception as e:
            self.logger.error(f"Failed to create indexes: {str(e)}")
            raise
    
    async def _prepare_cache_data(self) -> Optional[Dict[str, Any]]:
        """Prepare TCGA data for caching."""
        try:
            # Cache frequently accessed data
            cache_data = {
                "cancer_type_counts": {},
                "data_type_counts": {},
                "gene_expression_stats": {},
                "mutation_stats": {}
            }
            
            # Read processed data to generate cache
            processed_files = list(self.processed_data_path.rglob("*.parquet"))
            
            for file_path in processed_files:
                try:
                    data = pd.read_parquet(file_path)
                    
                    # Count by cancer type
                    if "cancer_type" in data.columns:
                        cancer_counts = data["cancer_type"].value_counts()
                        for cancer_type, count in cancer_counts.items():
                            cache_data["cancer_type_counts"][cancer_type] = cache_data["cancer_type_counts"].get(cancer_type, 0) + count
                    
                    # Count by data type
                    if "data_type" in data.columns:
                        data_type_counts = data["data_type"].value_counts()
                        for data_type, count in data_type_counts.items():
                            cache_data["data_type_counts"][data_type] = cache_data["data_type_counts"].get(data_type, 0) + count
                    
                    # Gene expression statistics
                    if "data_type" in data.columns and data["data_type"].iloc[0] == "gene_expression":
                        if "expression_value" in data.columns:
                            cache_data["gene_expression_stats"][file_path.stem] = {
                                "mean": float(data["expression_value"].mean()),
                                "std": float(data["expression_value"].std()),
                                "min": float(data["expression_value"].min()),
                                "max": float(data["expression_value"].max())
                            }
                    
                    # Mutation statistics
                    if "data_type" in data.columns and data["data_type"].iloc[0] == "mutations":
                        cache_data["mutation_stats"][file_path.stem] = {
                            "total_mutations": len(data),
                            "unique_genes": data["gene_id"].nunique() if "gene_id" in data.columns else 0
                        }
                
                except Exception as e:
                    self.logger.warning(f"Failed to process {file_path} for cache: {str(e)}")
            
            return cache_data
            
        except Exception as e:
            self.logger.error(f"Failed to prepare cache data: {str(e)}")
            return None
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of TCGA data."""
        summary = {
            "dataset_name": "tcga",
            "cancer_types": {},
            "data_types": {},
            "total_files": 0,
            "total_records": 0
        }
        
        try:
            # Count files and records by cancer type and data type
            processed_files = list(self.processed_data_path.rglob("*.parquet"))
            summary["total_files"] = len(processed_files)
            
            for file_path in processed_files:
                try:
                    data = pd.read_parquet(file_path)
                    summary["total_records"] += len(data)
                    
                    # Update cancer type counts
                    if "cancer_type" in data.columns:
                        cancer_type = data["cancer_type"].iloc[0]
                        if cancer_type not in summary["cancer_types"]:
                            summary["cancer_types"][cancer_type] = {"files": 0, "records": 0}
                        summary["cancer_types"][cancer_type]["files"] += 1
                        summary["cancer_types"][cancer_type]["records"] += len(data)
                    
                    # Update data type counts
                    if "data_type" in data.columns:
                        data_type = data["data_type"].iloc[0]
                        if data_type not in summary["data_types"]:
                            summary["data_types"][data_type] = {"files": 0, "records": 0}
                        summary["data_types"][data_type]["files"] += 1
                        summary["data_types"][data_type]["records"] += len(data)
                
                except Exception as e:
                    self.logger.warning(f"Failed to process {file_path} for summary: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate data summary: {str(e)}")
        
        return summary
    
    def _progress_callback(self, progress: float, downloaded: int, total: int) -> None:
        """Callback for download progress."""
        if int(progress) % 10 == 0:
            self.logger.info(f"Download progress: {progress:.1f}% ({downloaded}/{total} bytes)") 