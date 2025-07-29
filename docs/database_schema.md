# Database Schema Design

## 🗄️ Centralized Database Architecture

### Primary Database (Supabase PostgreSQL)
- **Connection Pooling**: Supabase handles connection pooling automatically
- **Authentication**: Supabase Auth for user management
- **Real-time**: Built-in real-time subscriptions
- **Storage**: Large object storage for genomic files

### Data Storage Strategy
- **PostgreSQL**: Metadata, user data, analysis results, small datasets
- **MinIO**: Large genomic files (BAM, VCF, FASTQ, expression matrices)
- **Redis**: Caching, session management, real-time data

## 📊 Unified Data Schema

### Core Tables

#### 1. datasets
```sql
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    source VARCHAR(100) NOT NULL, -- 'TCGA', '1000_GENOMES', 'ENCODE', etc.
    description TEXT,
    version VARCHAR(50),
    total_samples INTEGER,
    total_variants BIGINT,
    file_size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

#### 2. samples
```sql
CREATE TABLE samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id),
    sample_id VARCHAR(255) NOT NULL,
    external_id VARCHAR(255),
    sample_type VARCHAR(100), -- 'tumor', 'normal', 'cell_line'
    tissue_type VARCHAR(100),
    disease_type VARCHAR(100),
    age INTEGER,
    gender VARCHAR(10),
    ethnicity VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. variants
```sql
CREATE TABLE variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id),
    chromosome VARCHAR(10) NOT NULL,
    position BIGINT NOT NULL,
    reference_allele TEXT NOT NULL,
    alternate_allele TEXT NOT NULL,
    variant_type VARCHAR(50), -- 'SNP', 'INDEL', 'SV'
    quality_score DECIMAL,
    allele_frequency DECIMAL,
    pathogenicity_score DECIMAL,
    clinical_significance VARCHAR(50),
    annotations JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. gene_expression
```sql
CREATE TABLE gene_expression (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id),
    sample_id UUID REFERENCES samples(id),
    gene_id VARCHAR(100) NOT NULL,
    gene_name VARCHAR(255),
    expression_value DECIMAL,
    expression_unit VARCHAR(50),
    measurement_type VARCHAR(100), -- 'RNA-seq', 'microarray'
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5. drug_targets
```sql
CREATE TABLE drug_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drug_id VARCHAR(100) NOT NULL,
    drug_name VARCHAR(255),
    target_gene VARCHAR(100),
    target_protein VARCHAR(255),
    interaction_type VARCHAR(100),
    binding_affinity DECIMAL,
    source VARCHAR(100), -- 'DrugBank', 'ChEMBL'
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 6. literature_entities
```sql
CREATE TABLE literature_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pmid VARCHAR(20),
    title TEXT,
    abstract TEXT,
    entity_type VARCHAR(50), -- 'gene', 'disease', 'drug'
    entity_name VARCHAR(255),
    entity_id VARCHAR(100),
    confidence_score DECIMAL,
    source VARCHAR(100), -- 'PubMed', 'PMC'
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Analysis Tables

#### 7. analysis_jobs
```sql
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    job_type VARCHAR(100), -- 'variant_analysis', 'drug_response', 'biomarker_discovery'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    input_data JSONB,
    output_data JSONB,
    progress_percentage INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 8. model_predictions
```sql
CREATE TABLE model_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_job_id UUID REFERENCES analysis_jobs(id),
    model_type VARCHAR(100), -- 'variant_predictor', 'drug_response', 'biomarker'
    input_data JSONB,
    prediction_result JSONB,
    confidence_score DECIMAL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔗 Dataset-Specific Mappings

### TCGA Data
- **Samples**: Cancer samples with clinical metadata
- **Variants**: Somatic and germline variants
- **Expression**: RNA-seq expression data
- **Clinical**: Patient outcomes, treatment history

### 1000 Genomes
- **Samples**: Population samples
- **Variants**: Population frequency data
- **Ancestry**: Genetic ancestry information

### ENCODE
- **Samples**: Cell lines, tissues
- **Expression**: ChIP-seq, RNA-seq, ATAC-seq
- **Regulatory**: Transcription factor binding, chromatin states

### ClinVar
- **Variants**: Clinical significance annotations
- **Diseases**: Disease associations
- **Evidence**: Literature evidence levels

## 🚀 Implementation Strategy

1. **Phase 1**: Set up Supabase with core tables
2. **Phase 2**: Create data ingestion pipelines for each dataset
3. **Phase 3**: Implement unified query interface
4. **Phase 4**: Add caching and optimization layers

## 🔧 Connection Pooling Configuration

```python
# Database connection with pooling
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True
}
```

## 📈 Performance Considerations

- **Indexing**: Strategic indexes on frequently queried columns
- **Partitioning**: Large tables partitioned by dataset_id
- **Caching**: Redis for frequently accessed data
- **Archiving**: Old data moved to cold storage 