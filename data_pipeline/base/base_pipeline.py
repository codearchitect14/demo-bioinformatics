"""
Abstract base class for all dataset pipelines.

This module provides the foundation for implementing data ingestion pipelines
for various genomic datasets with standardized error handling, logging, and
data processing workflows.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json

import pandas as pd
from sqlalchemy.orm import Session

from utils.logging_utils import setup_logger
from utils.download_utils import DownloadManager
from .data_validator import DataValidator
from .data_transformer import DataTransformer


class BaseDatasetPipeline(ABC):
    """
    Abstract base class for dataset pipelines.
    
    Provides standardized methods for data download, validation, transformation,
    and loading with comprehensive error handling and logging.
    """
    
    def __init__(
        self,
        dataset_name: str,
        config: Dict[str, Any],
        db_session: Optional[Session] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize the pipeline.
        
        Args:
            dataset_name: Name of the dataset
            config: Pipeline configuration dictionary
            db_session: Database session for data loading
            cache_enabled: Whether to enable caching
        """
        self.dataset_name = dataset_name
        self.config = config
        self.db_session = db_session
        self.cache_enabled = cache_enabled
        
        # Initialize components
        self.logger = setup_logger(f"pipeline.{dataset_name}")
        self.download_manager = DownloadManager()
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        
        # Pipeline state
        self.start_time = None
        self.end_time = None
        self.total_records = 0
        self.processed_records = 0
        self.failed_records = 0
        self.validation_errors = []
        
        # Create data directories
        self._create_directories()
    
    def _create_directories(self) -> None:
        """Create necessary directories for data storage."""
        base_path = Path(self.config.get("data_path", "/data"))
        self.raw_data_path = base_path / self.dataset_name / "raw"
        self.processed_data_path = base_path / self.dataset_name / "processed"
        self.logs_path = base_path / self.dataset_name / "logs"
        
        for path in [self.raw_data_path, self.processed_data_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    async def run(self) -> Dict[str, Any]:
        """
        Execute the complete pipeline workflow.
        
        Returns:
            Dictionary containing pipeline execution results
        """
        self.start_time = datetime.now()
        self.logger.info(f"Starting {self.dataset_name} pipeline")
        
        try:
            # Execute pipeline stages
            await self._download_data()
            await self._validate_data()
            await self._transform_data()
            await self._load_data()
            await self._create_indexes()
            
            if self.cache_enabled:
                await self._update_cache()
            
            self.end_time = datetime.now()
            results = self._generate_results()
            
            self.logger.info(f"Pipeline completed successfully: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            self.end_time = datetime.now()
            return self._generate_error_results(e)
    
    @abstractmethod
    async def _download_data(self) -> None:
        """
        Download data from source.
        
        This method must be implemented by subclasses to handle
        dataset-specific download logic.
        """
        pass
    
    @abstractmethod
    async def _validate_data(self) -> None:
        """
        Validate downloaded data.
        
        This method must be implemented by subclasses to handle
        dataset-specific validation logic.
        """
        pass
    
    @abstractmethod
    async def _transform_data(self) -> None:
        """
        Transform data to unified schema.
        
        This method must be implemented by subclasses to handle
        dataset-specific transformation logic.
        """
        pass
    
    async def _load_data(self) -> None:
        """Load transformed data into database."""
        if not self.db_session:
            self.logger.warning("No database session provided, skipping data loading")
            return
        
        try:
            # Load data in batches
            batch_size = self.config.get("batch_size", 1000)
            processed_files = list(self.processed_data_path.glob("*.parquet"))
            
            for file_path in processed_files:
                df = pd.read_parquet(file_path)
                self.total_records += len(df)
                
                # Process in batches
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i + batch_size]
                    await self._load_batch(batch)
                    self.processed_records += len(batch)
                    
                    # Log progress
                    if self.processed_records % (batch_size * 10) == 0:
                        self.logger.info(f"Loaded {self.processed_records} records")
            
            self.logger.info(f"Data loading completed: {self.processed_records} records")
            
        except Exception as e:
            self.logger.error(f"Data loading failed: {str(e)}")
            raise
    
    async def _load_batch(self, batch: pd.DataFrame) -> None:
        """
        Load a batch of data into database.
        
        Args:
            batch: DataFrame containing data to load
        """
        # This method should be overridden by subclasses for dataset-specific loading
        pass
    
    async def _create_indexes(self) -> None:
        """Create database indexes for optimized queries."""
        if not self.db_session:
            return
        
        try:
            # Create indexes based on dataset configuration
            indexes = self.config.get("indexes", [])
            for index_config in indexes:
                await self._create_index(index_config)
            
            self.logger.info("Database indexes created successfully")
            
        except Exception as e:
            self.logger.error(f"Index creation failed: {str(e)}")
            raise
    
    async def _create_index(self, index_config: Dict[str, Any]) -> None:
        """
        Create a specific database index.
        
        Args:
            index_config: Index configuration dictionary
        """
        # This method should be overridden by subclasses for dataset-specific indexing
        pass
    
    async def _update_cache(self) -> None:
        """Update cache with frequently accessed data."""
        try:
            # Cache frequently accessed data
            cache_data = await self._prepare_cache_data()
            if cache_data:
                # Store in Redis or other cache
                self.logger.info("Cache updated successfully")
            
        except Exception as e:
            self.logger.error(f"Cache update failed: {str(e)}")
            # Don't fail the pipeline for cache errors
    
    async def _prepare_cache_data(self) -> Optional[Dict[str, Any]]:
        """
        Prepare data for caching.
        
        Returns:
            Dictionary containing data to cache
        """
        # This method should be overridden by subclasses
        return None
    
    def _generate_results(self) -> Dict[str, Any]:
        """Generate pipeline execution results."""
        duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            "dataset_name": self.dataset_name,
            "status": "success",
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": duration,
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "failed_records": self.failed_records,
            "validation_errors": len(self.validation_errors),
            "throughput": self.processed_records / duration if duration > 0 else 0
        }
    
    def _generate_error_results(self, error: Exception) -> Dict[str, Any]:
        """Generate error results for failed pipeline execution."""
        duration = (self.end_time - self.start_time).total_seconds()
        
        return {
            "dataset_name": self.dataset_name,
            "status": "failed",
            "error": str(error),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": duration,
            "total_records": self.total_records,
            "processed_records": self.processed_records,
            "failed_records": self.failed_records,
            "validation_errors": len(self.validation_errors)
        }
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        return {
            "dataset_name": self.dataset_name,
            "is_running": self.start_time and not self.end_time,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "processed_records": self.processed_records,
            "total_records": self.total_records,
            "progress_percentage": (
                (self.processed_records / self.total_records * 100) 
                if self.total_records > 0 else 0
            )
        }
    
    def cleanup(self) -> None:
        """Clean up temporary files and resources."""
        try:
            # Clean up temporary files
            temp_files = list(self.raw_data_path.glob("*.tmp"))
            for file_path in temp_files:
                file_path.unlink()
            
            self.logger.info("Cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}") 