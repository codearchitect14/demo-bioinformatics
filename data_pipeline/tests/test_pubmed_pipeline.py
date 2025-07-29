"""
Tests for PubMed data pipeline.

This module contains comprehensive tests for the PubMed pipeline including
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
from datetime import datetime

from ..datasets.pubmed_pipeline import PubMedPipeline


class TestPubMedPipeline:
    """Test suite for PubMed pipeline."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_article_data(self):
        """Create sample PubMed article data for testing."""
        return pd.DataFrame({
            "pmid": [12345678, 23456789, 34567890],
            "title": [
                "Genomics in Precision Medicine: A Comprehensive Review",
                "Bioinformatics Approaches to Cancer Genomics",
                "Genetic Variation and Drug Response Prediction"
            ],
            "abstract": [
                "This review discusses the role of genomics in precision medicine...",
                "Bioinformatics tools are essential for analyzing cancer genomics data...",
                "Understanding genetic variation is crucial for predicting drug response..."
            ],
            "authors": [
                '[{"last_name": "Smith", "first_name": "John"}, {"last_name": "Doe", "first_name": "Jane"}]',
                '[{"last_name": "Johnson", "first_name": "Bob"}]',
                '[{"last_name": "Williams", "first_name": "Alice"}]'
            ],
            "journal": ["Nature Genetics", "Bioinformatics", "Pharmacogenomics"],
            "publication_date": ["2023-01-15", "2023-02-20", "2023-03-10"],
            "doi": ["10.1038/ng.1234", "10.1093/bioinformatics/btx123", "10.2217/pgs-2023-001"],
            "keywords": [
                '["genomics", "precision medicine", "review"]',
                '["bioinformatics", "cancer", "genomics"]',
                '["genetic variation", "drug response", "prediction"]'
            ],
            "mesh_terms": [
                '["Genomics", "Precision Medicine", "Review"]',
                '["Bioinformatics", "Neoplasms", "Genomics"]',
                '["Genetic Variation", "Drug Response", "Prediction"]'
            ],
            "article_type": [
                '["Review", "Journal Article"]',
                '["Research Article", "Journal Article"]',
                '["Research Article", "Journal Article"]'
            ]
        })
    
    @pytest.fixture
    def sample_citation_data(self):
        """Create sample PubMed citation data for testing."""
        return pd.DataFrame({
            "citing_pmid": [12345678, 12345678, 23456789],
            "cited_pmid": [11111111, 22222222, 33333333],
            "citation_date": ["2023-01-15", "2023-01-15", "2023-02-20"],
            "citation_type": ["cited_in", "cited_in", "cited_in"]
        })
    
    @pytest.fixture
    def pipeline_config(self, temp_data_dir):
        """Create pipeline configuration for testing."""
        return {
            "data_path": str(temp_data_dir),
            "batch_size": 25,
            "max_retries": 2,
            "timeout": 60,
            "update_frequency": "daily",
            "pubmed_api_key": "test_api_key",
            "max_articles_per_request": 50,
            "delay_between_requests": 0.1,
            "search_terms": ["genomics", "bioinformatics"],
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "indexes": [
                {"name": "idx_pubmed_pmid", "columns": ["pmid"]},
                {"name": "idx_pubmed_search_term", "columns": ["search_term"]}
            ]
        }
    
    @pytest.fixture
    def mock_pipeline(self, pipeline_config):
        """Create a mock PubMed pipeline."""
        return PubMedPipeline(pipeline_config)
    
    def test_pipeline_initialization(self, pipeline_config):
        """Test pipeline initialization."""
        pipeline = PubMedPipeline(pipeline_config)
        
        assert pipeline.dataset_name == "pubmed"
        assert pipeline.config == pipeline_config
        assert pipeline.raw_data_path.exists()
        assert pipeline.processed_data_path.exists()
        assert pipeline.logs_path.exists()
        assert len(pipeline.search_terms) == 2
        assert "genomics" in pipeline.search_terms
        assert "bioinformatics" in pipeline.search_terms
        assert pipeline.pubmed_api_key == "test_api_key"
    
    def test_create_directories(self, pipeline_config):
        """Test directory creation."""
        pipeline = PubMedPipeline(pipeline_config)
        
        # Check that directories were created
        assert pipeline.raw_data_path.exists()
        assert pipeline.processed_data_path.exists()
        assert pipeline.logs_path.exists()
        
        # Check directory structure
        assert (pipeline.raw_data_path / "pubmed").exists()
        assert (pipeline.processed_data_path / "pubmed").exists()
        assert (pipeline.logs_path / "pubmed").exists()
    
    def test_transform_article_data(self, mock_pipeline, sample_article_data):
        """Test article data transformation."""
        transformed_data = mock_pipeline._transform_article_data(sample_article_data, "genomics")
        
        # Check that metadata was added
        assert "search_term" in transformed_data.columns
        assert "data_type" in transformed_data.columns
        assert "source_type" in transformed_data.columns
        assert "transformed_at" in transformed_data.columns
        assert "data_version" in transformed_data.columns
        
        # Check metadata values
        assert all(transformed_data["search_term"] == "genomics")
        assert all(transformed_data["data_type"] == "articles")
        assert all(transformed_data["source_type"] == "pubmed")
        assert all(transformed_data["data_version"] == "1.0")
        
        # Check that text features were added
        assert "abstract_length" in transformed_data.columns
        assert "word_count" in transformed_data.columns
        
        # Check that PMID is numeric
        assert transformed_data["pmid"].dtype in ['int64', 'Int64']
    
    def test_transform_citation_data(self, mock_pipeline, sample_citation_data):
        """Test citation data transformation."""
        transformed_data = mock_pipeline._transform_citation_data(sample_citation_data, "genomics")
        
        # Check that metadata was added
        assert "search_term" in transformed_data.columns
        assert "data_type" in transformed_data.columns
        assert "source_type" in transformed_data.columns
        
        # Check metadata values
        assert all(transformed_data["search_term"] == "genomics")
        assert all(transformed_data["data_type"] == "citations")
        assert all(transformed_data["source_type"] == "pubmed")
        
        # Check that PMIDs are numeric
        assert transformed_data["citing_pmid"].dtype in ['int64', 'Int64']
        assert transformed_data["cited_pmid"].dtype in ['int64', 'Int64']
    
    def test_clean_article_data(self, mock_pipeline, sample_article_data):
        """Test article data cleaning."""
        # Add some problematic data
        sample_article_data.loc[0, "title"] = "   Multiple   Spaces   "
        sample_article_data.loc[1, "abstract"] = ""
        sample_article_data.loc[2, "pmid"] = "invalid"
        
        cleaned_data = mock_pipeline._clean_article_data(sample_article_data)
        
        # Check that text was cleaned
        assert cleaned_data.loc[0, "title"] == "Multiple Spaces"
        
        # Check that empty abstract was handled
        assert pd.isna(cleaned_data.loc[1, "abstract"])
        
        # Check that invalid PMID was handled
        assert pd.isna(cleaned_data.loc[2, "pmid"])
        
        # Check that valid PMIDs are numeric
        assert cleaned_data["pmid"].dtype in ['int64', 'Int64', 'float64']
    
    def test_clean_citation_data(self, mock_pipeline, sample_citation_data):
        """Test citation data cleaning."""
        # Add some problematic data
        sample_citation_data.loc[0, "citing_pmid"] = "invalid"
        sample_citation_data.loc[1, "cited_pmid"] = "invalid"
        
        cleaned_data = mock_pipeline._clean_citation_data(sample_citation_data)
        
        # Check that invalid PMIDs were handled
        assert pd.isna(cleaned_data.loc[0, "citing_pmid"])
        assert pd.isna(cleaned_data.loc[1, "cited_pmid"])
        
        # Check that valid PMIDs are numeric
        assert cleaned_data["citing_pmid"].dtype in ['int64', 'Int64', 'float64']
        assert cleaned_data["cited_pmid"].dtype in ['int64', 'Int64', 'float64']
    
    def test_parse_pubmed_xml(self, mock_pipeline):
        """Test PubMed XML parsing."""
        # Create sample XML data
        xml_data = """
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test Article Title</ArticleTitle>
                        <Abstract>
                            <AbstractText>Test abstract text.</AbstractText>
                        </Abstract>
                        <AuthorList>
                            <Author>
                                <LastName>Smith</LastName>
                                <ForeName>John</ForeName>
                            </Author>
                        </AuthorList>
                    </Article>
                    <Journal>
                        <Title>Test Journal</Title>
                    </Journal>
                    <PubDate>
                        <Year>2023</Year>
                        <Month>01</Month>
                        <Day>15</Day>
                    </PubDate>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>
        """
        
        articles = mock_pipeline._parse_pubmed_xml(xml_data)
        
        # Check that article was parsed correctly
        assert len(articles) == 1
        article = articles[0]
        
        assert article["pmid"] == 12345678
        assert article["title"] == "Test Article Title"
        assert article["abstract"] == "Test abstract text."
        assert article["journal"] == "Test Journal"
        assert article["publication_date"] == "2023-01-15"
        assert "Smith" in article["authors"]
        assert "John" in article["authors"]
    
    def test_parse_citation_xml(self, mock_pipeline):
        """Test citation XML parsing."""
        # Create sample citation XML data
        xml_data = """
        <eLinkResult>
            <LinkSet>
                <LinkSetDb>
                    <LinkName>pubmed_pubmed_citedin</LinkName>
                    <Link>
                        <Id>11111111</Id>
                    </Link>
                    <Link>
                        <Id>22222222</Id>
                    </Link>
                </LinkSetDb>
            </LinkSet>
        </eLinkResult>
        """
        
        citations = mock_pipeline._parse_citation_xml(xml_data, "12345678")
        
        # Check that citations were parsed correctly
        assert len(citations) == 2
        
        assert citations[0]["citing_pmid"] == 12345678
        assert citations[0]["cited_pmid"] == 11111111
        assert citations[0]["citation_type"] == "cited_in"
        
        assert citations[1]["citing_pmid"] == 12345678
        assert citations[1]["cited_pmid"] == 22222222
        assert citations[1]["citation_type"] == "cited_in"
    
    def test_extract_article_data(self, mock_pipeline):
        """Test article data extraction from XML element."""
        # Create sample XML element
        xml_element = """
        <PubmedArticle>
            <MedlineCitation>
                <PMID>12345678</PMID>
                <Article>
                    <ArticleTitle>Test Article</ArticleTitle>
                    <Abstract>
                        <AbstractText>Test abstract.</AbstractText>
                    </Abstract>
                    <AuthorList>
                        <Author>
                            <LastName>Smith</LastName>
                            <ForeName>John</ForeName>
                        </Author>
                    </AuthorList>
                </Article>
                <Journal>
                    <Title>Test Journal</Title>
                </Journal>
                <PubDate>
                    <Year>2023</Year>
                    <Month>01</Month>
                    <Day>15</Day>
                </PubDate>
            </MedlineCitation>
        </PubmedArticle>
        """
        
        # Parse XML and extract article data
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_element)
        article = mock_pipeline._extract_article_data(root)
        
        # Check extracted data
        assert article is not None
        assert article["pmid"] == 12345678
        assert article["title"] == "Test Article"
        assert article["abstract"] == "Test abstract."
        assert article["journal"] == "Test Journal"
        assert article["publication_date"] == "2023-01-15"
        assert "Smith" in article["authors"]
        assert "John" in article["authors"]
    
    def test_data_validation(self, mock_pipeline, sample_article_data):
        """Test data validation."""
        # Test schema validation
        is_valid, errors = mock_pipeline.validator.validate_schema(
            sample_article_data, 
            mock_pipeline.schemas["articles"]
        )
        
        assert is_valid, f"Schema validation failed: {errors}"
        
        # Test completeness validation
        required_fields = ["pmid", "title", "abstract"]
        is_complete, completeness_scores = mock_pipeline.validator.validate_completeness(
            sample_article_data, 
            required_fields
        )
        
        assert is_complete, f"Completeness validation failed: {completeness_scores}"
    
    def test_data_summary_generation(self, mock_pipeline, sample_article_data, temp_data_dir):
        """Test data summary generation."""
        # Create processed data files
        processed_dir = temp_data_dir / "pubmed" / "processed" / "genomics"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save sample data as parquet
        transformed_data = mock_pipeline._transform_article_data(sample_article_data, "genomics")
        transformed_data.to_parquet(processed_dir / "articles_transformed.parquet", index=False)
        
        # Generate summary
        summary = mock_pipeline.get_data_summary()
        
        # Check summary structure
        assert "dataset_name" in summary
        assert "search_terms" in summary
        assert "data_types" in summary
        assert "total_files" in summary
        assert "total_records" in summary
        
        # Check summary values
        assert summary["dataset_name"] == "pubmed"
        assert summary["total_files"] >= 1
        assert summary["total_records"] >= 3
        assert "genomics" in summary["search_terms"]
        assert "articles" in summary["data_types"]
    
    @pytest.mark.asyncio
    async def test_pipeline_execution_mock(self, pipeline_config):
        """Test pipeline execution with mocked API calls."""
        with patch('data_pipeline.datasets.pubmed_pipeline.DownloadManager') as mock_download_manager:
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
            
            # Mock API responses
            with patch.object(PubMedPipeline, '_search_articles') as mock_search:
                mock_search.return_value = ["12345678", "23456789"]
                
                with patch.object(PubMedPipeline, '_fetch_article_details') as mock_fetch:
                    mock_fetch.return_value = [
                        {"pmid": 12345678, "title": "Test Article", "abstract": "Test abstract"}
                    ]
                    
                    with patch.object(PubMedPipeline, '_fetch_citations') as mock_citations:
                        mock_citations.return_value = [
                            {"citing_pmid": 12345678, "cited_pmid": 11111111}
                        ]
                        
                        # Create pipeline
                        pipeline = PubMedPipeline(pipeline_config)
                        
                        # Mock file operations
                        with patch('pathlib.Path.exists', return_value=True):
                            with patch('pathlib.Path.stat') as mock_stat:
                                mock_stat.return_value.st_mtime = 0  # Old file
                                
                                # Run pipeline
                                results = await pipeline.run()
                                
                                # Check results
                                assert results["status"] == "success"
                                assert results["dataset_name"] == "pubmed"
                                assert "duration_seconds" in results
                                assert "total_records" in results
                                assert "processed_records" in results
    
    def test_error_handling(self, pipeline_config):
        """Test error handling in pipeline."""
        # Test with invalid configuration
        invalid_config = pipeline_config.copy()
        invalid_config["data_path"] = "/invalid/path"
        
        with pytest.raises(Exception):
            PubMedPipeline(invalid_config)
    
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
    async def test_cache_preparation(self, mock_pipeline, sample_article_data, temp_data_dir):
        """Test cache data preparation."""
        # Create processed data files
        processed_dir = temp_data_dir / "pubmed" / "processed" / "genomics"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save sample data as parquet
        transformed_data = mock_pipeline._transform_article_data(sample_article_data, "genomics")
        transformed_data.to_parquet(processed_dir / "articles_transformed.parquet", index=False)
        
        # Prepare cache data
        cache_data = await mock_pipeline._prepare_cache_data()
        
        # Check cache data structure
        assert cache_data is not None
        assert "search_term_counts" in cache_data
        assert "data_type_counts" in cache_data
        assert "publication_timeline" in cache_data
        assert "top_journals" in cache_data
        assert "top_authors" in cache_data
        
        # Check that cache data contains expected information
        assert len(cache_data["search_term_counts"]) > 0
        assert len(cache_data["data_type_counts"]) > 0
    
    def test_search_terms_configuration(self, pipeline_config):
        """Test search terms configuration."""
        pipeline = PubMedPipeline(pipeline_config)
        
        # Check that search terms are properly configured
        assert len(pipeline.search_terms) == 2
        assert "genomics" in pipeline.search_terms
        assert "bioinformatics" in pipeline.search_terms
        
        # Check that search terms are strings
        for term in pipeline.search_terms:
            assert isinstance(term, str)
            assert len(term) > 0
    
    def test_date_range_configuration(self, pipeline_config):
        """Test date range configuration."""
        pipeline = PubMedPipeline(pipeline_config)
        
        # Check that date range is properly configured
        assert pipeline.start_date == "2023-01-01"
        assert pipeline.end_date == "2023-12-31"
        
        # Check that dates are in correct format
        from datetime import datetime
        try:
            datetime.strptime(pipeline.start_date, "%Y-%m-%d")
            datetime.strptime(pipeline.end_date, "%Y-%m-%d")
        except ValueError:
            pytest.fail("Date format is invalid")


class TestPubMedDataQuality:
    """Test suite for PubMed data quality checks."""
    
    def test_article_data_quality(self):
        """Test article data quality validation."""
        from ..base.data_validator import DataValidator
        
        validator = DataValidator()
        
        # Test valid article data
        valid_data = pd.DataFrame({
            "pmid": [12345678, 23456789],
            "title": ["Test Article 1", "Test Article 2"],
            "abstract": ["Test abstract 1.", "Test abstract 2."],
            "journal": ["Test Journal 1", "Test Journal 2"]
        })
        
        is_valid, errors = validator.validate_genomic_data(valid_data, "articles")
        assert is_valid, f"Valid article data failed validation: {errors}"
        
        # Test invalid article data
        invalid_data = pd.DataFrame({
            "pmid": [12345678, -1],  # Invalid PMID
            "title": ["Test Article", ""],  # Empty title
            "abstract": ["Test abstract", None],  # Missing abstract
            "journal": ["Test Journal", "Test Journal"]
        })
        
        is_valid, errors = validator.validate_genomic_data(invalid_data, "articles")
        assert not is_valid, "Invalid article data should fail validation"
        assert len(errors) > 0
    
    def test_citation_data_quality(self):
        """Test citation data quality validation."""
        from ..base.data_validator import DataValidator
        
        validator = DataValidator()
        
        # Test valid citation data
        valid_data = pd.DataFrame({
            "citing_pmid": [12345678, 23456789],
            "cited_pmid": [11111111, 22222222],
            "citation_type": ["cited_in", "cited_in"]
        })
        
        is_valid, errors = validator.validate_genomic_data(valid_data, "citations")
        assert is_valid, f"Valid citation data failed validation: {errors}"
        
        # Test invalid citation data
        invalid_data = pd.DataFrame({
            "citing_pmid": [12345678, -1],  # Invalid PMID
            "cited_pmid": [11111111, 0],  # Invalid PMID
            "citation_type": ["cited_in", "invalid_type"]  # Invalid type
        })
        
        is_valid, errors = validator.validate_genomic_data(invalid_data, "citations")
        assert not is_valid, "Invalid citation data should fail validation"
        assert len(errors) > 0


class TestPubMedAPIIntegration:
    """Test suite for PubMed API integration."""
    
    @pytest.mark.asyncio
    async def test_search_articles_api(self, pipeline_config):
        """Test article search API integration."""
        pipeline = PubMedPipeline(pipeline_config)
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock successful API response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "esearchresult": {
                    "idlist": ["12345678", "23456789"]
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test search
            article_ids = await pipeline._search_articles("genomics")
            
            # Check results
            assert len(article_ids) == 2
            assert "12345678" in article_ids
            assert "23456789" in article_ids
    
    @pytest.mark.asyncio
    async def test_fetch_article_details_api(self, pipeline_config):
        """Test article details API integration."""
        pipeline = PubMedPipeline(pipeline_config)
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock successful API response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = """
            <PubmedArticleSet>
                <PubmedArticle>
                    <MedlineCitation>
                        <PMID>12345678</PMID>
                        <Article>
                            <ArticleTitle>Test Article</ArticleTitle>
                            <Abstract>
                                <AbstractText>Test abstract.</AbstractText>
                            </Abstract>
                        </Article>
                    </MedlineCitation>
                </PubmedArticle>
            </PubmedArticleSet>
            """
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test fetch
            articles = await pipeline._fetch_article_details(["12345678"])
            
            # Check results
            assert len(articles) == 1
            assert articles[0]["pmid"] == 12345678
            assert articles[0]["title"] == "Test Article"


if __name__ == "__main__":
    pytest.main([__file__]) 