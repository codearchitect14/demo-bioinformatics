# TCGA Data Pipeline Guide

## Overview

The TCGA (The Cancer Genome Atlas) pipeline is designed to download, process, and load comprehensive cancer genomics data into the genomics platform. TCGA provides multi-omics data including gene expression, mutations, clinical data, and more for various cancer types.

## 🧬 Data Types Supported

### 1. **Clinical Data**
- Patient demographics and clinical information
- Tumor characteristics and staging
- Survival and follow-up data
- Treatment information

### 2. **Gene Expression Data**
- RNA-seq expression data
- Gene-level expression values (TPM, FPKM, counts)
- Transcript-level expression data

### 3. **Mutation Data**
- Somatic mutations (SNPs, indels, structural variants)
- Variant annotation and functional impact
- Mutation frequency and distribution

### 4. **Copy Number Variation**
- DNA copy number alterations
- Amplifications and deletions
- Segmental changes

### 5. **Methylation Data**
- DNA methylation profiles
- Beta values and methylation levels
- Epigenetic modifications

### 6. **Protein Expression**
- Protein expression levels
- Immunohistochemistry data
- Protein abundance measurements

## 🏗️ Architecture

### Pipeline Components

```
TCGA Pipeline
├── Data Download
│   ├── GDC API Integration
│   ├── File Discovery
│   └── Concurrent Downloads
├── Data Validation
│   ├── Schema Validation
│   ├── Quality Checks
│   └── Format Verification
├── Data Transformation
│   ├── Format Conversion
│   ├── Schema Mapping
│   └── Data Cleaning
└── Data Loading
    ├── Database Storage
    ├── Index Creation
    └── Cache Management
```

### Data Flow

```
GDC API → Download → Validate → Transform → Database → Index → Cache
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TCGA_DATA_PATH="/data/tcga"
export TCGA_BATCH_SIZE="100"
export TCGA_MAX_RETRIES="3"
export TCGA_TIMEOUT="600"
export TCGA_CANCER_TYPES="BRCA,LUAD,LUSC,COAD,READ"
```

### 2. Run Pipeline

```bash
# Run TCGA pipeline
python -m data_pipeline.scripts.run_tcga_pipeline

# Or run with custom configuration
python -m data_pipeline.scripts.run_tcga_pipeline --config custom_config.json
```

### 3. Monitor Progress

```bash
# Check pipeline status
tail -f /data/tcga/logs/tcga_pipeline.log

# View results
cat /data/tcga/logs/tcga_results_*.json
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TCGA_DATA_PATH` | `/data/tcga` | Base path for TCGA data |
| `TCGA_BATCH_SIZE` | `100` | Batch size for processing |
| `TCGA_MAX_RETRIES` | `3` | Maximum download retries |
| `TCGA_TIMEOUT` | `600` | Request timeout (seconds) |
| `TCGA_UPDATE_FREQUENCY` | `weekly` | Update frequency |
| `TCGA_CANCER_TYPES` | `BRCA,LUAD,LUSC...` | Cancer types to process |

### Configuration File

```json
{
  "data_path": "/data/tcga",
  "batch_size": 100,
  "max_retries": 3,
  "timeout": 600,
  "update_frequency": "weekly",
  "cancer_types": [
    "BRCA", "LUAD", "LUSC", "COAD", "READ", 
    "STAD", "LIHC", "KIRC", "KIRP", "THCA"
  ],
  "indexes": [
    {"name": "idx_tcga_patient_id", "columns": ["patient_id"]},
    {"name": "idx_tcga_cancer_type", "columns": ["cancer_type"]},
    {"name": "idx_tcga_data_type", "columns": ["data_type"]},
    {"name": "idx_tcga_gene_id", "columns": ["gene_id"]},
    {"name": "idx_tcga_chromosome_position", "columns": ["chromosome", "position"]}
  ]
}
```

## 📊 Cancer Types Supported

### Primary Cancer Types

| Cancer Type | Full Name | Data Available |
|-------------|-----------|----------------|
| BRCA | Breast Invasive Carcinoma | Clinical, Expression, Mutations |
| LUAD | Lung Adenocarcinoma | Clinical, Expression, Mutations |
| LUSC | Lung Squamous Cell Carcinoma | Clinical, Expression, Mutations |
| COAD | Colon Adenocarcinoma | Clinical, Expression, Mutations |
| READ | Rectum Adenocarcinoma | Clinical, Expression, Mutations |
| STAD | Stomach Adenocarcinoma | Clinical, Expression, Mutations |
| LIHC | Liver Hepatocellular Carcinoma | Clinical, Expression, Mutations |
| KIRC | Kidney Renal Clear Cell Carcinoma | Clinical, Expression, Mutations |
| KIRP | Kidney Renal Papillary Cell Carcinoma | Clinical, Expression, Mutations |
| THCA | Thyroid Carcinoma | Clinical, Expression, Mutations |

### Additional Cancer Types

- BLCA (Bladder Urothelial Carcinoma)
- CESC (Cervical Squamous Cell Carcinoma)
- ESCA (Esophageal Carcinoma)
- HNSC (Head and Neck Squamous Cell Carcinoma)
- OV (Ovarian Serous Cystadenocarcinoma)
- PAAD (Pancreatic Adenocarcinoma)
- PRAD (Prostate Adenocarcinoma)
- SKCM (Skin Cutaneous Melanoma)
- UCEC (Uterine Corpus Endometrial Carcinoma)

## 🔧 Data Processing

### Clinical Data Processing

```python
# Example clinical data transformation
clinical_data = {
    "submitter_id": "TCGA-01-0001",
    "age_at_index": 45,
    "gender": "female",
    "tumor_stage": "stage i",
    "vital_status": "alive"
}

# Transformed to unified schema
transformed_data = {
    "patient_id": "TCGA-01-0001",
    "age": 45,
    "gender": "FEMALE",
    "tumor_stage": "stage i",
    "vital_status": "ALIVE",
    "cancer_type": "BRCA",
    "data_type": "clinical",
    "source_type": "tcga"
}
```

### Gene Expression Processing

```python
# Example expression data transformation
expression_data = {
    "gene_id": "ENSG00000139618",
    "gene_name": "BRCA2",
    "expression_value": 12.5,
    "expression_unit": "TPM"
}

# Transformed to unified schema
transformed_data = {
    "gene_id": "ENSG00000139618",
    "gene_name": "BRCA2",
    "expression_value": 12.5,
    "expression_unit": "TPM",
    "cancer_type": "BRCA",
    "data_type": "gene_expression",
    "source_type": "tcga"
}
```

### Mutation Data Processing

```python
# Example mutation data transformation
mutation_data = {
    "chromosome": "13",
    "position": 32315474,
    "reference_allele": "A",
    "alternate_allele": "G",
    "gene_id": "ENSG00000139618",
    "gene_name": "BRCA2"
}

# Transformed to unified schema
transformed_data = {
    "chromosome": "13",
    "position": 32315474,
    "reference_allele": "A",
    "alternate_allele": "G",
    "gene_id": "ENSG00000139618",
    "gene_name": "BRCA2",
    "cancer_type": "BRCA",
    "data_type": "mutations",
    "source_type": "tcga"
}
```

## 📈 Data Quality Assurance

### Validation Checks

1. **Schema Validation**
   - Required columns present
   - Data types correct
   - Value ranges valid

2. **Completeness Validation**
   - Missing value detection
   - Required field completeness
   - Data coverage assessment

3. **Consistency Validation**
   - Cross-field consistency
   - Business rule validation
   - Format standardization

4. **Quality Metrics**
   - Data freshness
   - Source reliability
   - Processing accuracy

### Quality Reports

```json
{
  "dataset_name": "tcga",
  "cancer_types": {
    "BRCA": {
      "files": 150,
      "records": 15000,
      "completeness": 0.95,
      "quality_score": 0.92
    }
  },
  "data_types": {
    "clinical": {
      "files": 50,
      "records": 5000,
      "completeness": 0.98,
      "quality_score": 0.95
    },
    "gene_expression": {
      "files": 50,
      "records": 5000000,
      "completeness": 0.93,
      "quality_score": 0.90
    }
  }
}
```

## 🔍 Monitoring and Logging

### Log Levels

- **INFO**: General pipeline progress
- **DEBUG**: Detailed processing information
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures

### Log Files

```
/data/tcga/logs/
├── tcga_pipeline.log          # Main pipeline log
├── tcga_pipeline_errors.log   # Error log
├── tcga_pipeline_performance.log  # Performance metrics
└── tcga_results_*.json        # Pipeline results
```

### Performance Metrics

- Download speed (bytes/second)
- Processing throughput (records/second)
- Memory usage
- CPU utilization
- Network I/O

## 🧪 Testing

### Run Tests

```bash
# Run all TCGA pipeline tests
pytest data_pipeline/tests/test_tcga_pipeline.py -v

# Run specific test categories
pytest data_pipeline/tests/test_tcga_pipeline.py::TestTCGAPipeline -v
pytest data_pipeline/tests/test_tcga_pipeline.py::TestTCGADataQuality -v

# Run with coverage
pytest data_pipeline/tests/test_tcga_pipeline.py --cov=data_pipeline.datasets.tcga_pipeline
```

### Test Categories

1. **Unit Tests**
   - Pipeline initialization
   - Data transformation
   - File processing

2. **Integration Tests**
   - End-to-end pipeline execution
   - Database integration
   - API interactions

3. **Data Quality Tests**
   - Validation accuracy
   - Transformation correctness
   - Schema compliance

## 🚨 Troubleshooting

### Common Issues

1. **Download Failures**
   ```bash
   # Check network connectivity
   curl -I https://api.gdc.cancer.gov
   
   # Verify API access
   curl https://api.gdc.cancer.gov/status
   ```

2. **Memory Issues**
   ```bash
   # Reduce batch size
   export TCGA_BATCH_SIZE="50"
   
   # Monitor memory usage
   htop
   ```

3. **Disk Space**
   ```bash
   # Check available space
   df -h /data/tcga
   
   # Clean old files
   find /data/tcga -name "*.tmp" -delete
   ```

### Error Recovery

1. **Resume Failed Downloads**
   ```bash
   # Pipeline automatically retries failed downloads
   # Check retry configuration in environment variables
   ```

2. **Data Validation Failures**
   ```bash
   # Review validation logs
   tail -f /data/tcga/logs/tcga_pipeline_errors.log
   
   # Fix data issues and re-run
   ```

3. **Database Connection Issues**
   ```bash
   # Check database connectivity
   # Verify connection pool settings
   # Review database logs
   ```

## 📚 API Reference

### TCGAPipeline Class

```python
class TCGAPipeline(BaseDatasetPipeline):
    def __init__(self, config: Dict[str, Any], db_session=None, cache_enabled: bool = True)
    
    async def run() -> Dict[str, Any]
    async def _download_data() -> None
    async def _validate_data() -> None
    async def _transform_data() -> None
    def get_data_summary() -> Dict[str, Any]
```

### Configuration Schema

```python
{
    "data_path": str,           # Base data directory
    "batch_size": int,          # Processing batch size
    "max_retries": int,         # Download retry attempts
    "timeout": int,             # Request timeout (seconds)
    "cancer_types": List[str],  # Cancer types to process
    "indexes": List[Dict]       # Database indexes
}
```

## 🔗 Related Documentation

- [Data Pipeline Overview](../README.md)
- [ClinVar Pipeline Guide](./clinvar_pipeline_guide.md)
- [PubMed Pipeline Guide](./pubmed_pipeline_guide.md)
- [Database Schema](../database_schema.md)
- [API Documentation](../../backend/docs/api.md)

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review pipeline logs
3. Run diagnostic tests
4. Contact the development team

---

**Last Updated**: July 2024  
**Version**: 1.0.0  
**Maintainer**: GenomicsAI Team 