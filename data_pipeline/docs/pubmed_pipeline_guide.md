# PubMed Data Pipeline Guide

## Overview

The PubMed pipeline is designed to download, process, and load biomedical literature data from the National Center for Biotechnology Information (NCBI) PubMed database. This pipeline enables literature mining, text analysis, and knowledge discovery in genomics and bioinformatics research.

## 📚 Data Types Supported

### 1. **Article Metadata**
- Article titles and abstracts
- Author information and affiliations
- Journal details and publication dates
- Digital Object Identifiers (DOIs)
- PubMed IDs (PMIDs)

### 2. **Citation Networks**
- Article-to-article citations
- Citation relationships and networks
- Citation analysis and impact metrics
- Temporal citation patterns

### 3. **MeSH Terms**
- Medical Subject Headings
- Controlled vocabulary for indexing
- Hierarchical classification
- Topic categorization

### 4. **Keywords and Tags**
- Author-provided keywords
- Automatic keyword extraction
- Topic modeling support
- Content classification

### 5. **Full-Text Data** (Optional)
- Full article text when available
- Supplementary materials
- Figure and table captions
- References and bibliographies

## 🏗️ Architecture

### Pipeline Components

```
PubMed Pipeline
├── Data Discovery
│   ├── NCBI E-utilities API
│   ├── Search Term Processing
│   └── Date Range Filtering
├── Data Download
│   ├── Article Metadata
│   ├── Citation Networks
│   └── Rate-Limited Requests
├── Data Processing
│   ├── XML Parsing
│   ├── Text Cleaning
│   └── Metadata Extraction
└── Data Storage
    ├── Structured Database
    ├── Full-Text Storage
    └── Search Indexing
```

### Data Flow

```
Search Terms → API Query → Download → Parse → Clean → Transform → Database → Index
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PUBMED_DATA_PATH="/data/pubmed"
export PUBMED_API_KEY="your_ncbi_api_key"  # Optional but recommended
export PUBMED_SEARCH_TERMS="genomics,bioinformatics,genetic variation"
export PUBMED_START_DATE="2020-01-01"
export PUBMED_END_DATE="2024-01-01"
```

### 2. Run Pipeline

```bash
# Run PubMed pipeline
python -m data_pipeline.scripts.run_pubmed_pipeline

# Or run with custom configuration
python -m data_pipeline.scripts.run_pubmed_pipeline --config custom_config.json
```

### 3. Monitor Progress

```bash
# Check pipeline status
tail -f /data/pubmed/logs/pubmed_pipeline.log

# View results
cat /data/pubmed/logs/pubmed_results_*.json
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PUBMED_DATA_PATH` | `/data/pubmed` | Base path for PubMed data |
| `PUBMED_API_KEY` | `` | NCBI API key (recommended) |
| `PUBMED_BATCH_SIZE` | `50` | Batch size for processing |
| `PUBMED_MAX_RETRIES` | `3` | Maximum download retries |
| `PUBMED_TIMEOUT` | `300` | Request timeout (seconds) |
| `PUBMED_MAX_ARTICLES` | `100` | Max articles per request |
| `PUBMED_DELAY` | `0.34` | Delay between requests (seconds) |
| `PUBMED_SEARCH_TERMS` | `genomics,bioinformatics...` | Search terms |
| `PUBMED_START_DATE` | `2020-01-01` | Start date for search |
| `PUBMED_END_DATE` | `today` | End date for search |

### Configuration File

```json
{
  "data_path": "/data/pubmed",
  "batch_size": 50,
  "max_retries": 3,
  "timeout": 300,
  "update_frequency": "daily",
  "pubmed_api_key": "your_ncbi_api_key",
  "max_articles_per_request": 100,
  "delay_between_requests": 0.34,
  "search_terms": [
    "genomics",
    "bioinformatics", 
    "genetic variation",
    "gene expression",
    "cancer genomics",
    "precision medicine",
    "drug discovery",
    "biomarker",
    "pharmacogenomics",
    "genetic testing"
  ],
  "start_date": "2020-01-01",
  "end_date": "2024-01-01",
  "indexes": [
    {"name": "idx_pubmed_pmid", "columns": ["pmid"]},
    {"name": "idx_pubmed_search_term", "columns": ["search_term"]},
    {"name": "idx_pubmed_data_type", "columns": ["data_type"]},
    {"name": "idx_pubmed_publication_date", "columns": ["publication_date"]}
  ]
}
```

## 🔍 Search Terms and Queries

### Predefined Search Categories

#### **Genomics and Bioinformatics**
- `genomics`
- `bioinformatics`
- `genetic variation`
- `gene expression`
- `genome sequencing`

#### **Cancer Research**
- `cancer genomics`
- `precision oncology`
- `tumor profiling`
- `cancer biomarkers`
- `therapeutic targets`

#### **Drug Discovery**
- `drug discovery`
- `pharmacogenomics`
- `drug targets`
- `drug response`
- `therapeutic development`

#### **Clinical Applications**
- `precision medicine`
- `genetic testing`
- `clinical genomics`
- `diagnostic biomarkers`
- `personalized medicine`

### Custom Search Queries

```python
# Complex search queries
search_terms = [
    '"cancer genomics"[Title/Abstract] AND "precision medicine"[Title/Abstract]',
    '"drug discovery"[Title/Abstract] AND "AI"[Title/Abstract]',
    '"genetic variation"[Title/Abstract] AND "drug response"[Title/Abstract]',
    '"biomarker discovery"[Title/Abstract] AND "machine learning"[Title/Abstract]'
]
```

## 📊 Data Processing

### Article Data Processing

```python
# Example article data transformation
article_data = {
    "pmid": 12345678,
    "title": "Genomics in Precision Medicine: A Comprehensive Review",
    "abstract": "This review discusses the role of genomics...",
    "authors": [
        {"last_name": "Smith", "first_name": "John"},
        {"last_name": "Doe", "first_name": "Jane"}
    ],
    "journal": "Nature Genetics",
    "publication_date": "2023-01-15",
    "doi": "10.1038/ng.1234"
}

# Transformed to unified schema
transformed_data = {
    "pmid": 12345678,
    "title": "Genomics in Precision Medicine: A Comprehensive Review",
    "abstract": "This review discusses the role of genomics...",
    "authors": '[{"last_name": "Smith", "first_name": "John"}, {"last_name": "Doe", "first_name": "Jane"}]',
    "journal": "Nature Genetics",
    "publication_date": "2023-01-15",
    "doi": "10.1038/ng.1234",
    "search_term": "genomics",
    "data_type": "articles",
    "source_type": "pubmed",
    "abstract_length": 45,
    "word_count": 8
}
```

### Citation Data Processing

```python
# Example citation data transformation
citation_data = {
    "citing_pmid": 12345678,
    "cited_pmid": 11111111,
    "citation_date": "2023-01-15",
    "citation_type": "cited_in"
}

# Transformed to unified schema
transformed_data = {
    "citing_pmid": 12345678,
    "cited_pmid": 11111111,
    "citation_date": "2023-01-15",
    "citation_type": "cited_in",
    "search_term": "genomics",
    "data_type": "citations",
    "source_type": "pubmed"
}
```

### Text Feature Extraction

```python
# Text analysis features
text_features = {
    "abstract_length": len(abstract),
    "word_count": len(abstract.split()),
    "sentence_count": len(abstract.split('.')),
    "avg_word_length": sum(len(word) for word in abstract.split()) / len(abstract.split()),
    "unique_words": len(set(abstract.lower().split())),
    "vocabulary_richness": len(set(abstract.lower().split())) / len(abstract.split())
}
```

## 📈 Data Quality Assurance

### Validation Checks

1. **Schema Validation**
   - Required fields present
   - Data types correct
   - Value ranges valid

2. **Content Validation**
   - Text quality assessment
   - Language detection
   - Duplicate detection

3. **Citation Validation**
   - Citation relationship integrity
   - Circular reference detection
   - Citation network validation

4. **Metadata Validation**
   - Author information completeness
   - Journal information accuracy
   - Date format validation

### Quality Reports

```json
{
  "dataset_name": "pubmed",
  "search_terms": {
    "genomics": {
      "articles": 1500,
      "citations": 5000,
      "completeness": 0.95,
      "quality_score": 0.92
    }
  },
  "data_types": {
    "articles": {
      "total": 5000,
      "with_abstract": 4800,
      "with_authors": 4900,
      "with_doi": 3000,
      "quality_score": 0.94
    },
    "citations": {
      "total": 15000,
      "valid_relationships": 14800,
      "quality_score": 0.98
    }
  }
}
```

## 🔍 Monitoring and Logging

### Log Levels

- **INFO**: General pipeline progress
- **DEBUG**: Detailed API interactions
- **WARNING**: Rate limit warnings
- **ERROR**: API failures and data issues

### Log Files

```
/data/pubmed/logs/
├── pubmed_pipeline.log          # Main pipeline log
├── pubmed_pipeline_errors.log   # Error log
├── pubmed_pipeline_api.log      # API interaction log
├── pubmed_pipeline_performance.log  # Performance metrics
└── pubmed_results_*.json        # Pipeline results
```

### Performance Metrics

- API request rate (requests/second)
- Download throughput (articles/second)
- Processing speed (records/second)
- Memory usage
- Network I/O

## 🧪 Testing

### Run Tests

```bash
# Run all PubMed pipeline tests
pytest data_pipeline/tests/test_pubmed_pipeline.py -v

# Run specific test categories
pytest data_pipeline/tests/test_pubmed_pipeline.py::TestPubMedPipeline -v
pytest data_pipeline/tests/test_pubmed_pipeline.py::TestPubMedDataQuality -v
pytest data_pipeline/tests/test_pubmed_pipeline.py::TestPubMedAPIIntegration -v

# Run with coverage
pytest data_pipeline/tests/test_pubmed_pipeline.py --cov=data_pipeline.datasets.pubmed_pipeline
```

### Test Categories

1. **Unit Tests**
   - Pipeline initialization
   - Data transformation
   - XML parsing

2. **Integration Tests**
   - API interactions
   - End-to-end pipeline
   - Database integration

3. **Data Quality Tests**
   - Validation accuracy
   - Transformation correctness
   - Schema compliance

## 🚨 Troubleshooting

### Common Issues

1. **API Rate Limiting**
   ```bash
   # Check current rate limits
   curl -I https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
   
   # Increase delay between requests
   export PUBMED_DELAY="1.0"
   ```

2. **API Key Issues**
   ```bash
   # Verify API key
   curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=genomics&api_key=YOUR_KEY"
   
   # Get new API key from NCBI
   # https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/
   ```

3. **Memory Issues**
   ```bash
   # Reduce batch size
   export PUBMED_BATCH_SIZE="25"
   
   # Monitor memory usage
   htop
   ```

4. **Network Issues**
   ```bash
   # Check network connectivity
   ping eutils.ncbi.nlm.nih.gov
   
   # Test API endpoint
   curl https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=12345678&retmode=xml
   ```

### Error Recovery

1. **Resume Failed Downloads**
   ```bash
   # Pipeline automatically retries failed requests
   # Check retry configuration in environment variables
   ```

2. **Data Validation Failures**
   ```bash
   # Review validation logs
   tail -f /data/pubmed/logs/pubmed_pipeline_errors.log
   
   # Fix data issues and re-run
   ```

3. **API Connection Issues**
   ```bash
   # Check API status
   curl https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi
   
   # Verify rate limits
   # NCBI allows 3 requests per second without API key
   # NCBI allows 10 requests per second with API key
   ```

## 📚 API Reference

### PubMedPipeline Class

```python
class PubMedPipeline(BaseDatasetPipeline):
    def __init__(self, config: Dict[str, Any], db_session=None, cache_enabled: bool = True)
    
    async def run() -> Dict[str, Any]
    async def _download_data() -> None
    async def _validate_data() -> None
    async def _transform_data() -> None
    async def _search_articles(search_term: str) -> List[str]
    async def _fetch_article_details(article_ids: List[str]) -> List[Dict]
    def _parse_pubmed_xml(xml_data: str) -> List[Dict]
    def get_data_summary() -> Dict[str, Any]
```

### Configuration Schema

```python
{
    "data_path": str,                    # Base data directory
    "batch_size": int,                   # Processing batch size
    "max_retries": int,                  # Download retry attempts
    "timeout": int,                      # Request timeout (seconds)
    "pubmed_api_key": str,               # NCBI API key
    "max_articles_per_request": int,     # Max articles per API call
    "delay_between_requests": float,     # Delay between requests
    "search_terms": List[str],           # Search terms
    "start_date": str,                   # Start date (YYYY-MM-DD)
    "end_date": str,                     # End date (YYYY-MM-DD)
    "indexes": List[Dict]                # Database indexes
}
```

## 🔗 Related Documentation

- [Data Pipeline Overview](../README.md)
- [ClinVar Pipeline Guide](./clinvar_pipeline_guide.md)
- [TCGA Pipeline Guide](./tcga_pipeline_guide.md)
- [Database Schema](../database_schema.md)
- [API Documentation](../../backend/docs/api.md)

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review pipeline logs
3. Run diagnostic tests
4. Contact the development team

## 📋 NCBI API Guidelines

### Rate Limits
- **Without API Key**: 3 requests per second
- **With API Key**: 10 requests per second
- **Burst Requests**: Up to 10 requests in a burst

### Best Practices
- Use API keys for production applications
- Implement proper error handling
- Respect rate limits
- Cache results when possible
- Use appropriate retry logic

### API Endpoints
- **E-utilities Base URL**: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
- **Search**: esearch.fcgi
- **Fetch**: efetch.fcgi
- **Link**: elink.fcgi
- **Summary**: esummary.fcgi

---

**Last Updated**: July 2024  
**Version**: 1.0.0  
**Maintainer**: GenomicsAI Team 