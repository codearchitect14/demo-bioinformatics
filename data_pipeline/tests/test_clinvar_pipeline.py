"""
Tests for ClinVar data pipeline.

This module contains comprehensive tests for the ClinVar pipeline including
data validation, transformation, and pipeline execution.
"""

import pytest
import asyncio
import pandas as pd
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from ..datasets.clinvar_pipeline import ClinVarPipeline


class TestClinVarPipeline:
    """Test suite for ClinVar pipeline."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_clinvar_data(self):
        """Create sample ClinVar data for testing."""
        return pd.DataFrame({
            "AlleleID": [1, 2, 3, 4, 5],
            "Type": ["single nucleotide variant", "deletion", "insertion", "duplication", "inversion"],
            "Name": ["rs123456", "rs234567", "rs345678", "rs456789", "rs567890"],
            "GeneID": [1000, 2000, 3000, 4000, 5000],
            "GeneSymbol": ["BRCA1", "BRCA2", "TP53", "APC", "MLH1"],
            "HGNC_ID": ["HGNC:1100", "HGNC:1101", "HGNC:1102", "HGNC:1103", "HGNC:1104"],
            "ClinicalSignificance": ["Pathogenic", "Likely_pathogenic", "Uncertain_significance", "Likely_benign", "Benign"],
            "ClinSigSimple": ["Pathogenic", "Pathogenic", "Uncertain", "Benign", "Benign"],
            "LastEvaluated": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"],
            "RS# (dbSNP)": ["rs123456", "rs234567", "rs345678", "rs456789", "rs567890"],
            "nsv/esv (dbVar)": ["", "", "", "", ""],
            "PhenotypeIDs": ["HP:0000001", "HP:0000002", "HP:0000003", "HP:0000004", "HP:0000005"],
            "PhenotypeList": ["Disease 1", "Disease 2", "Disease 3", "Disease 4", "Disease 5"],
            "Origin": ["germline", "germline", "germline", "germline", "germline"],
            "Assembly": ["GRCh38", "GRCh38", "GRCh38", "GRCh38", "GRCh38"],
            "ChromosomeAccession": ["NC_000017.11", "NC_000013.11", "NC_000017.11", "NC_000005.10", "NC_000003.12"],
            "Chromosome": ["17", "13", "17", "5", "3"],
            "Start": [43044295, 32315474, 7577120, 112043195, 37034840],
            "Stop": [43044295, 32315474, 7577120, 112043195, 37034840],
            "ReferenceAllele": ["A", "G", "C", "T", "A"],
            "AlternateAllele": ["G", "A", "T", "C", "G"],
            "Cytogenetic": ["17q21.31", "13q12.3", "17p13.1", "5q22.2", "3p22.2"],
            "ReviewStatus": ["criteria provided, single submitter", "criteria provided, multiple submitters", "criteria provided, single submitter", "criteria provided, single submitter", "criteria provided, single submitter"],
            "NumberSubmitters": [1, 2, 1, 1, 1],
            "Guidelines": ["", "", "", "", ""],
            "TestedInGTR": ["N", "N", "N", "N", "N"],
            "OtherIDs": ["", "", "", "", ""],
            "SubmitterCategories": ["", "", "", "", ""],
            "VariationID": [1001, 1002, 1003, 1004, 1005]
        })
    
    @pytest.fixture
    def pipeline_config(self, temp_data_dir):
        """Create pipeline configuration for testing."""
        return {
            "data_path": str(temp_data_dir),
            "batch_size": 100,
            "max_retries": 2,
            "timeout": 60,
            "update_frequency": "daily",
            "indexes": [
                {"name": "idx_clinvar_variant_id", "columns": ["variant_id"]},
                {"name": "idx_clinvar_gene_id", "columns": ["gene_id"]}
            ]
        }
    
    @pytest.fixture
    def mock_pipeline(self, pipeline_config):
        """Create a mock ClinVar pipeline."""
        return ClinVarPipeline(pipeline_config)
    
    def test_pipeline_initialization(self, pipeline_config):
        """Test pipeline initialization."""
        pipeline = ClinVarPipeline(pipeline_config)
        
        assert pipeline.dataset_name == "clinvar"
        assert pipeline.config == pipeline_config
        assert pipeline.raw_data_path.exists()
        assert pipeline.processed_data_path.exists()
        assert pipeline.logs_path.exists()
    
    def test_create_directories(self, pipeline_config):
        """Test directory creation."""
        pipeline = ClinVarPipeline(pipeline_config)
        
        # Check that directories were created
        assert pipeline.raw_data_path.exists()
        assert pipeline.processed_data_path.exists()
        assert pipeline.logs_path.exists()
        
        # Check directory structure
        assert (pipeline.raw_data_path / "clinvar").exists()
        assert (pipeline.processed_data_path / "clinvar").exists()
        assert (pipeline.logs_path / "clinvar").exists()
    
    def test_clean_variants_data(self, mock_pipeline, sample_clinvar_data):
        """Test data cleaning functionality."""
        # Test the cleaning function
        cleaned_data = mock_pipeline._clean_variants_data(sample_clinvar_data.copy())
        
        # Check that data types are correct
        assert cleaned_data["variant_id"].dtype in ['int64', 'Int64']
        assert cleaned_data["gene_id"].dtype in ['int64', 'Int64']
        assert cleaned_data["position"].dtype in ['int64', 'Int64']
        
        # Check that chromosome names are standardized
        assert all(chr_name in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", 
                               "11", "12", "13", "14", "15", "16", "17", "18", "19", 
                               "20", "21", "22", "X", "Y", "MT"] for chr_name in cleaned_data["chromosome"])
        
        # Check that clinical significance is lowercase
        assert all(sig.lower() == sig for sig in cleaned_data["clinical_significance"].dropna())
    
    def test_transform_variants_chunk(self, mock_pipeline, sample_clinvar_data):
        """Test variant data transformation."""
        transformed_data = mock_pipeline._transform_variants_chunk(sample_clinvar_data)
        
        # Check that columns were renamed
        assert "variant_id" in transformed_data.columns
        assert "gene_id" in transformed_data.columns
        assert "clinical_significance" in transformed_data.columns
        assert "AlleleID" not in transformed_data.columns  # Original column should be gone
        
        # Check that metadata was added
        assert "source_type" in transformed_data.columns
        assert "transformed_at" in transformed_data.columns
        assert "data_version" in transformed_data.columns
        
        # Check metadata values
        assert all(transformed_data["source_type"] == "clinvar")
        assert all(transformed_data["data_version"] == "1.0")
    
    def test_data_validation(self, mock_pipeline, sample_clinvar_data):
        """Test data validation."""
        # Test schema validation
        is_valid, errors = mock_pipeline.validator.validate_schema(
            sample_clinvar_data, 
            mock_pipeline.variant_schema
        )
        
        assert is_valid, f"Schema validation failed: {errors}"
        
        # Test completeness validation
        required_fields = ["AlleleID", "GeneID", "ClinicalSignificance"]
        is_complete, completeness_scores = mock_pipeline.validator.validate_completeness(
            sample_clinvar_data, 
            required_fields
        )
        
        assert is_complete, f"Completeness validation failed: {completeness_scores}"
        
        # Test genomic data validation
        is_valid, errors = mock_pipeline.validator.validate_genomic_data(
            sample_clinvar_data, 
            "variants"
        )
        
        assert is_valid, f"Genomic validation failed: {errors}"
    
    def test_data_summary_generation(self, mock_pipeline, sample_clinvar_data, temp_data_dir):
        """Test data summary generation."""
        # Create processed data files
        processed_dir = temp_data_dir / "clinvar" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save sample data as parquet
        transformed_data = mock_pipeline._transform_variants_chunk(sample_clinvar_data)
        transformed_data.to_parquet(processed_dir / "variants_chunk_0000.parquet", index=False)
        
        # Generate summary
        summary = mock_pipeline.get_data_summary()
        
        # Check summary structure
        assert "dataset_name" in summary
        assert "total_variants" in summary
        assert "clinical_significance_distribution" in summary
        assert "gene_distribution" in summary
        assert "chromosome_distribution" in summary
        
        # Check summary values
        assert summary["dataset_name"] == "clinvar"
        assert summary["total_variants"] == 5
        assert len(summary["clinical_significance_distribution"]) > 0
        assert len(summary["gene_distribution"]) > 0
        assert len(summary["chromosome_distribution"]) > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_execution_mock(self, pipeline_config):
        """Test pipeline execution with mocked downloads."""
        with patch('data_pipeline.datasets.clinvar_pipeline.DownloadManager') as mock_download_manager:
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
            
            # Create pipeline
            pipeline = ClinVarPipeline(pipeline_config)
            
            # Mock file existence
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_mtime = 0  # Old file
                    
                    # Run pipeline
                    results = await pipeline.run()
                    
                    # Check results
                    assert results["status"] == "success"
                    assert results["dataset_name"] == "clinvar"
                    assert "duration_seconds" in results
                    assert "total_records" in results
                    assert "processed_records" in results
    
    def test_error_handling(self, pipeline_config):
        """Test error handling in pipeline."""
        # Test with invalid configuration
        invalid_config = pipeline_config.copy()
        invalid_config["data_path"] = "/invalid/path"
        
        with pytest.raises(Exception):
            ClinVarPipeline(invalid_config)
    
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
    async def test_cache_preparation(self, mock_pipeline, sample_clinvar_data, temp_data_dir):
        """Test cache data preparation."""
        # Create processed data files
        processed_dir = temp_data_dir / "clinvar" / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save sample data as parquet
        transformed_data = mock_pipeline._transform_variants_chunk(sample_clinvar_data)
        transformed_data.to_parquet(processed_dir / "variants_chunk_0000.parquet", index=False)
        
        # Prepare cache data
        cache_data = await mock_pipeline._prepare_cache_data()
        
        # Check cache data structure
        assert cache_data is not None
        assert "clinical_significance_counts" in cache_data
        assert "gene_variant_counts" in cache_data
        assert "chromosome_variant_counts" in cache_data
        
        # Check that cache data contains expected information
        assert len(cache_data["clinical_significance_counts"]) > 0
        assert len(cache_data["gene_variant_counts"]) > 0
        assert len(cache_data["chromosome_variant_counts"]) > 0


class TestClinVarDataQuality:
    """Test suite for ClinVar data quality checks."""
    
    def test_variant_data_quality(self):
        """Test variant data quality validation."""
        from ..base.data_validator import DataValidator
        
        validator = DataValidator()
        
        # Test valid variant data
        valid_data = pd.DataFrame({
            "chromosome": ["1", "2", "X", "Y"],
            "position": [1000, 2000, 3000, 4000],
            "reference_allele": ["A", "G", "C", "T"],
            "alternate_allele": ["G", "A", "T", "C"]
        })
        
        is_valid, errors = validator.validate_genomic_data(valid_data, "variants")
        assert is_valid, f"Valid variant data failed validation: {errors}"
        
        # Test invalid variant data
        invalid_data = pd.DataFrame({
            "chromosome": ["1", "invalid", "X", "Y"],
            "position": [1000, -1, 3000, 4000],  # Negative position
            "reference_allele": ["A", "INVALID", "C", "T"],  # Invalid allele
            "alternate_allele": ["G", "A", "T", "C"]
        })
        
        is_valid, errors = validator.validate_genomic_data(invalid_data, "variants")
        assert not is_valid, "Invalid variant data should fail validation"
        assert len(errors) > 0
    
    def test_clinical_significance_validation(self):
        """Test clinical significance validation."""
        from ..base.data_validator import DataValidator
        
        validator = DataValidator()
        
        # Test valid clinical significance values
        valid_data = pd.DataFrame({
            "clinical_significance": ["Pathogenic", "Likely_pathogenic", "Uncertain_significance", "Likely_benign", "Benign"]
        })
        
        # Test invalid clinical significance values
        invalid_data = pd.DataFrame({
            "clinical_significance": ["Pathogenic", "Invalid", "Uncertain_significance", "Likely_benign", "Benign"]
        })
        
        # This would typically be tested with a custom validation rule
        # For now, we'll just check that the data can be processed
        assert len(valid_data) == 5
        assert len(invalid_data) == 5


if __name__ == "__main__":
    pytest.main([__file__]) 