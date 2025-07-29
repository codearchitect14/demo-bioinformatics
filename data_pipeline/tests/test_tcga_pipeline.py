"""
Tests for TCGA data pipeline.

This module contains comprehensive tests for the TCGA pipeline including
data validation, transformation, and pipeline execution.
"""

import pytest
import asyncio
import pandas as pd
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from ..datasets.tcga_pipeline import TCGAPipeline


class TestTCGAPipeline:
    """Test suite for TCGA pipeline."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_clinical_data(self):
        """Create sample TCGA clinical data for testing."""
        return pd.DataFrame({
            "submitter_id": ["TCGA-01-0001", "TCGA-01-0002", "TCGA-01-0003"],
            "project_id": ["TCGA-BRCA", "TCGA-BRCA", "TCGA-BRCA"],
            "age_at_index": [45, 52, 38],
            "gender": ["female", "male", "female"],
            "race": ["white", "black", "asian"],
            "ethnicity": ["not hispanic or latino", "not hispanic or latino", "hispanic or latino"],
            "vital_status": ["alive", "dead", "alive"],
            "days_to_death": [None, 365, None],
            "days_to_last_follow_up": [730, None, 365],
            "tumor_stage": ["stage i", "stage ii", "stage iii"],
            "tumor_grade": ["g1", "g2", "g3"],
            "primary_diagnosis": ["breast cancer", "breast cancer", "breast cancer"],
            "tumor_type": ["primary tumor", "primary tumor", "primary tumor"]
        })
    
    @pytest.fixture
    def sample_expression_data(self):
        """Create sample TCGA gene expression data for testing."""
        return pd.DataFrame({
            "gene_id": ["ENSG00000139618", "ENSG00000157764", "ENSG00000141510"],
            "gene_name": ["BRCA2", "BRAF", "TP53"],
            "expression_value": [12.5, 8.3, 15.7],
            "expression_unit": ["TPM", "TPM", "TPM"],
            "sample_id": ["TCGA-01-0001", "TCGA-01-0001", "TCGA-01-0001"]
        })
    
    @pytest.fixture
    def sample_mutation_data(self):
        """Create sample TCGA mutation data for testing."""
        return pd.DataFrame({
            "chromosome": ["13", "7", "17"],
            "position": [32315474, 140453136, 7577120],
            "reference_allele": ["A", "T", "C"],
            "alternate_allele": ["G", "A", "T"],
            "variant_type": ["SNP", "SNP", "SNP"],
            "gene_id": ["ENSG00000139618", "ENSG00000157764", "ENSG00000141510"],
            "gene_name": ["BRCA2", "BRAF", "TP53"],
            "sample_id": ["TCGA-01-0001", "TCGA-01-0001", "TCGA-01-0001"],
            "mutation_type": ["missense_variant", "missense_variant", "missense_variant"]
        })
    
    @pytest.fixture
    def pipeline_config(self, temp_data_dir):
        """Create pipeline configuration for testing."""
        return {
            "data_path": str(temp_data_dir),
            "batch_size": 50,
            "max_retries": 2,
            "timeout": 60,
            "update_frequency": "weekly",
            "cancer_types": ["BRCA", "LUAD"],
            "indexes": [
                {"name": "idx_tcga_patient_id", "columns": ["patient_id"]},
                {"name": "idx_tcga_cancer_type", "columns": ["cancer_type"]}
            ]
        }
    
    @pytest.fixture
    def mock_pipeline(self, pipeline_config):
        """Create a mock TCGA pipeline."""
        return TCGAPipeline(pipeline_config)
    
    def test_pipeline_initialization(self, pipeline_config):
        """Test pipeline initialization."""
        pipeline = TCGAPipeline(pipeline_config)
        
        assert pipeline.dataset_name == "tcga"
        assert pipeline.config == pipeline_config
        assert pipeline.raw_data_path.exists()
        assert pipeline.processed_data_path.exists()
        assert pipeline.logs_path.exists()
        assert len(pipeline.cancer_types) == 2
        assert "BRCA" in pipeline.cancer_types
        assert "LUAD" in pipeline.cancer_types
    
    def test_create_directories(self, pipeline_config):
        """Test directory creation."""
        pipeline = TCGAPipeline(pipeline_config)
        
        # Check that directories were created
        assert pipeline.raw_data_path.exists()
        assert pipeline.processed_data_path.exists()
        assert pipeline.logs_path.exists()
        
        # Check directory structure
        assert (pipeline.raw_data_path / "tcga").exists()
        assert (pipeline.processed_data_path / "tcga").exists()
        assert (pipeline.logs_path / "tcga").exists()
    
    def test_transform_clinical_data(self, mock_pipeline, sample_clinical_data):
        """Test clinical data transformation."""
        transformed_data = mock_pipeline._transform_clinical_data(sample_clinical_data, "BRCA")
        
        # Check that columns were renamed
        assert "patient_id" in transformed_data.columns
        assert "age" in transformed_data.columns
        assert "submitter_id" not in transformed_data.columns  # Original column should be gone
        
        # Check that metadata was added
        assert "cancer_type" in transformed_data.columns
        assert "data_type" in transformed_data.columns
        assert "source_type" in transformed_data.columns
        assert "transformed_at" in transformed_data.columns
        assert "data_version" in transformed_data.columns
        
        # Check metadata values
        assert all(transformed_data["cancer_type"] == "BRCA")
        assert all(transformed_data["data_type"] == "clinical")
        assert all(transformed_data["source_type"] == "tcga")
        assert all(transformed_data["data_version"] == "1.0")
    
    def test_transform_expression_data(self, mock_pipeline, sample_expression_data):
        """Test gene expression data transformation."""
        transformed_data = mock_pipeline._transform_expression_data(sample_expression_data, "BRCA")
        
        # Check that metadata was added
        assert "cancer_type" in transformed_data.columns
        assert "data_type" in transformed_data.columns
        assert "source_type" in transformed_data.columns
        
        # Check metadata values
        assert all(transformed_data["cancer_type"] == "BRCA")
        assert all(transformed_data["data_type"] == "gene_expression")
        assert all(transformed_data["source_type"] == "tcga")
        
        # Check that expression values are numeric
        assert transformed_data["expression_value"].dtype in ['float64', 'float32']
    
    def test_transform_mutation_data(self, mock_pipeline, sample_mutation_data):
        """Test mutation data transformation."""
        transformed_data = mock_pipeline._transform_mutation_data(sample_mutation_data, "BRCA")
        
        # Check that metadata was added
        assert "cancer_type" in transformed_data.columns
        assert "data_type" in transformed_data.columns
        assert "source_type" in transformed_data.columns
        
        # Check metadata values
        assert all(transformed_data["cancer_type"] == "BRCA")
        assert all(transformed_data["data_type"] == "mutations")
        assert all(transformed_data["source_type"] == "tcga")
        
        # Check that position values are numeric
        assert transformed_data["position"].dtype in ['int64', 'Int64']
    
    def test_clean_clinical_data(self, mock_pipeline, sample_clinical_data):
        """Test clinical data cleaning."""
        # Add some problematic data
        sample_clinical_data.loc[0, "age_at_index"] = "Unknown"
        sample_clinical_data.loc[1, "gender"] = "unknown"
        
        cleaned_data = mock_pipeline._clean_clinical_data(sample_clinical_data)
        
        # Check that problematic values were handled
        assert pd.isna(cleaned_data.loc[0, "age"])
        assert cleaned_data.loc[1, "gender"] == "UNKNOWN"
        
        # Check that numeric columns are properly typed
        assert cleaned_data["age"].dtype in ['float64', 'Int64']
    
    def test_clean_expression_data(self, mock_pipeline, sample_expression_data):
        """Test expression data cleaning."""
        # Add some problematic data
        sample_expression_data.loc[0, "expression_value"] = "N/A"
        sample_expression_data.loc[1, "expression_value"] = "invalid"
        
        cleaned_data = mock_pipeline._clean_expression_data(sample_expression_data)
        
        # Check that problematic values were handled
        assert pd.isna(cleaned_data.loc[0, "expression_value"])
        assert pd.isna(cleaned_data.loc[1, "expression_value"])
        
        # Check that expression values are numeric
        assert cleaned_data["expression_value"].dtype in ['float64', 'float32']
    
    def test_clean_mutation_data(self, mock_pipeline, sample_mutation_data):
        """Test mutation data cleaning."""
        # Add some problematic data
        sample_mutation_data.loc[0, "chromosome"] = "chr13"
        sample_mutation_data.loc[1, "position"] = "invalid"
        
        cleaned_data = mock_pipeline._clean_mutation_data(sample_mutation_data)
        
        # Check that chromosome names were standardized
        assert cleaned_data.loc[0, "chromosome"] == "13"
        
        # Check that invalid position was handled
        assert pd.isna(cleaned_data.loc[1, "position"])
        
        # Check that position values are numeric
        assert cleaned_data["position"].dtype in ['int64', 'Int64']
    
    def test_read_json_file(self, mock_pipeline, temp_data_dir):
        """Test JSON file reading."""
        # Create test JSON file
        test_data = {
            "patient_id": "TCGA-01-0001",
            "age": 45,
            "gender": "female",
            "clinical_info": {
                "tumor_stage": "stage i",
                "tumor_grade": "g1"
            }
        }
        
        json_file = temp_data_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(test_data, f)
        
        # Read JSON file
        data = mock_pipeline._read_json_file(json_file)
        
        # Check that data was read correctly
        assert data is not None
        assert len(data) == 1
        assert "patient_id" in data.columns
        assert "clinical_info.tumor_stage" in data.columns
    
    def test_read_tsv_file(self, mock_pipeline, temp_data_dir):
        """Test TSV file reading."""
        # Create test TSV file
        test_data = pd.DataFrame({
            "gene_id": ["ENSG00000139618", "ENSG00000157764"],
            "expression_value": [12.5, 8.3]
        })
        
        tsv_file = temp_data_dir / "test.tsv"
        test_data.to_csv(tsv_file, sep='\t', index=False)
        
        # Read TSV file
        data = mock_pipeline._read_tsv_file(tsv_file)
        
        # Check that data was read correctly
        assert data is not None
        assert len(data) == 2
        assert "gene_id" in data.columns
        assert "expression_value" in data.columns
    
    def test_flatten_json(self, mock_pipeline):
        """Test JSON flattening."""
        nested_data = {
            "patient_id": "TCGA-01-0001",
            "clinical_info": {
                "tumor_stage": "stage i",
                "tumor_grade": "g1"
            },
            "genomic_data": {
                "mutations": ["mutation1", "mutation2"]
            }
        }
        
        flattened = mock_pipeline._flatten_json(nested_data)
        
        # Check that nested structure was flattened
        assert "patient_id" in flattened
        assert "clinical_info.tumor_stage" in flattened
        assert "clinical_info.tumor_grade" in flattened
        assert "genomic_data.mutations" in flattened
        
        # Check values
        assert flattened["patient_id"] == "TCGA-01-0001"
        assert flattened["clinical_info.tumor_stage"] == "stage i"
        assert flattened["genomic_data.mutations"] == '["mutation1", "mutation2"]'
    
    def test_data_validation(self, mock_pipeline, sample_clinical_data):
        """Test data validation."""
        # Test schema validation
        is_valid, errors = mock_pipeline.validator.validate_schema(
            sample_clinical_data, 
            mock_pipeline.schemas["clinical"]
        )
        
        assert is_valid, f"Schema validation failed: {errors}"
        
        # Test completeness validation
        required_fields = ["submitter_id", "age_at_index", "gender"]
        is_complete, completeness_scores = mock_pipeline.validator.validate_completeness(
            sample_clinical_data, 
            required_fields
        )
        
        assert is_complete, f"Completeness validation failed: {completeness_scores}"
    
    def test_data_summary_generation(self, mock_pipeline, sample_clinical_data, temp_data_dir):
        """Test data summary generation."""
        # Create processed data files
        processed_dir = temp_data_dir / "tcga" / "processed" / "BRCA" / "clinical"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save sample data as parquet
        transformed_data = mock_pipeline._transform_clinical_data(sample_clinical_data, "BRCA")
        transformed_data.to_parquet(processed_dir / "clinical_transformed.parquet", index=False)
        
        # Generate summary
        summary = mock_pipeline.get_data_summary()
        
        # Check summary structure
        assert "dataset_name" in summary
        assert "cancer_types" in summary
        assert "data_types" in summary
        assert "total_files" in summary
        assert "total_records" in summary
        
        # Check summary values
        assert summary["dataset_name"] == "tcga"
        assert summary["total_files"] >= 1
        assert summary["total_records"] >= 3
        assert "BRCA" in summary["cancer_types"]
        assert "clinical" in summary["data_types"]
    
    @pytest.mark.asyncio
    async def test_pipeline_execution_mock(self, pipeline_config):
        """Test pipeline execution with mocked downloads."""
        with patch('data_pipeline.datasets.tcga_pipeline.DownloadManager') as mock_download_manager:
            # Mock download manager
            mock_dm = AsyncMock()
            mock_dm.download_with_retry.return_value = {
                "success": True,
                "url": "test_url",
                "destination": "test_dest",
                "bytes_downloaded": 1000,
                "duration": 10.0,
                "speed_bytes_per_sec": 100.0
            }
            mock_download_manager.return_value.__aenter__.return_value = mock_dm
            
            # Mock GDC API query
            with patch.object(TCGAPipeline, '_query_gdc_files') as mock_query:
                mock_query.return_value = [
                    {"file_id": "test_id", "file_name": "test.tsv"}
                ]
                
                # Create pipeline
                pipeline = TCGAPipeline(pipeline_config)
                
                # Mock file existence
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('pathlib.Path.stat') as mock_stat:
                        mock_stat.return_value.st_mtime = 0  # Old file
                        
                        # Run pipeline
                        results = await pipeline.run()
                        
                        # Check results
                        assert results["status"] == "success"
                        assert results["dataset_name"] == "tcga"
                        assert "duration_seconds" in results
                        assert "total_records" in results
                        assert "processed_records" in results
    
    def test_error_handling(self, pipeline_config):
        """Test error handling in pipeline."""
        # Test with invalid configuration
        invalid_config = pipeline_config.copy()
        invalid_config["data_path"] = "/invalid/path"
        
        with pytest.raises(Exception):
            TCGAPipeline(invalid_config)
    
    def test_progress_callback(self, mock_pipeline):
        """Test progress callback functionality."""
        # Test progress callback
        mock_pipeline._progress_callback(50.0, 500, 1000)
        
        # The callback should not raise any exceptions
        # We can't easily test the logging output, but we can ensure it doesn't crash
    
    def test_cleanup_functionality(self, mock_pipeline):
        """Test cleanup functionality."""
        # Create a temporary file
        temp_file = mock_pipeline.raw_data_path / "test.tmp"
        temp_file.touch()
        
        # Run cleanup
        mock_pipeline.cleanup()
        
        # Check that temporary file was removed
        assert not temp_file.exists()
    
    @pytest.mark.asyncio
    async def test_cache_preparation(self, mock_pipeline, sample_clinical_data, temp_data_dir):
        """Test cache data preparation."""
        # Create processed data files
        processed_dir = temp_data_dir / "tcga" / "processed" / "BRCA" / "clinical"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save sample data as parquet
        transformed_data = mock_pipeline._transform_clinical_data(sample_clinical_data, "BRCA")
        transformed_data.to_parquet(processed_dir / "clinical_transformed.parquet", index=False)
        
        # Prepare cache data
        cache_data = await mock_pipeline._prepare_cache_data()
        
        # Check cache data structure
        assert cache_data is not None
        assert "cancer_type_counts" in cache_data
        assert "data_type_counts" in cache_data
        assert "gene_expression_stats" in cache_data
        assert "mutation_stats" in cache_data
        
        # Check that cache data contains expected information
        assert len(cache_data["cancer_type_counts"]) > 0
        assert len(cache_data["data_type_counts"]) > 0


class TestTCGADataQuality:
    """Test suite for TCGA data quality checks."""
    
    def test_clinical_data_quality(self):
        """Test clinical data quality validation."""
        from ..base.data_validator import DataValidator
        
        validator = DataValidator()
        
        # Test valid clinical data
        valid_data = pd.DataFrame({
            "age": [45, 52, 38],
            "gender": ["female", "male", "female"],
            "vital_status": ["alive", "dead", "alive"]
        })
        
        is_valid, errors = validator.validate_genomic_data(valid_data, "clinical")
        assert is_valid, f"Valid clinical data failed validation: {errors}"
        
        # Test invalid clinical data
        invalid_data = pd.DataFrame({
            "age": [45, -5, 150],  # Invalid ages
            "gender": ["female", "invalid", "male"],  # Invalid gender
            "vital_status": ["alive", "dead", "unknown"]  # Invalid status
        })
        
        is_valid, errors = validator.validate_genomic_data(invalid_data, "clinical")
        assert not is_valid, "Invalid clinical data should fail validation"
        assert len(errors) > 0
    
    def test_expression_data_quality(self):
        """Test expression data quality validation."""
        from ..base.data_validator import DataValidator
        
        validator = DataValidator()
        
        # Test valid expression data
        valid_data = pd.DataFrame({
            "gene_id": ["ENSG00000139618", "ENSG00000157764"],
            "expression_value": [12.5, 8.3]
        })
        
        is_valid, errors = validator.validate_genomic_data(valid_data, "expression")
        assert is_valid, f"Valid expression data failed validation: {errors}"
        
        # Test invalid expression data
        invalid_data = pd.DataFrame({
            "gene_id": ["ENSG00000139618", "ENSG00000157764"],
            "expression_value": [12.5, -5.0]  # Negative expression
        })
        
        is_valid, errors = validator.validate_genomic_data(invalid_data, "expression")
        assert not is_valid, "Invalid expression data should fail validation"
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__]) 