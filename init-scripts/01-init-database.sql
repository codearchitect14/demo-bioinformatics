-- Genomics Platform Database Initialization Script
-- This script creates the core database schema for the AI-powered genomics platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create core tables

-- 1. datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source VARCHAR(100) NOT NULL, -- 'TCGA', '1000_GENOMES', 'ENCODE', 'CLINVAR', 'PUBMED', etc.
    description TEXT,
    version VARCHAR(50),
    total_samples INTEGER,
    total_variants BIGINT,
    file_size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- 2. samples table
CREATE TABLE IF NOT EXISTS samples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
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

-- 3. variants table
CREATE TABLE IF NOT EXISTS variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
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

-- 4. gene_expression table
CREATE TABLE IF NOT EXISTS gene_expression (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    sample_id UUID REFERENCES samples(id) ON DELETE CASCADE,
    gene_id VARCHAR(100) NOT NULL,
    gene_name VARCHAR(255),
    expression_value DECIMAL,
    expression_unit VARCHAR(50),
    measurement_type VARCHAR(100), -- 'RNA-seq', 'microarray'
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. drug_targets table
CREATE TABLE IF NOT EXISTS drug_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    drug_id VARCHAR(100) NOT NULL,
    drug_name VARCHAR(255),
    target_gene VARCHAR(100),
    target_protein VARCHAR(255),
    interaction_type VARCHAR(100),
    binding_affinity DECIMAL,
    source VARCHAR(100), -- 'DrugBank', 'ChEMBL'
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. literature_entities table
CREATE TABLE IF NOT EXISTS literature_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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

-- 7. analysis_jobs table
CREATE TABLE IF NOT EXISTS analysis_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID, -- Will reference auth.users when auth is set up
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

-- 8. model_predictions table
CREATE TABLE IF NOT EXISTS model_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_job_id UUID REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    model_type VARCHAR(100), -- 'variant_predictor', 'drug_response', 'biomarker'
    input_data JSONB,
    prediction_result JSONB,
    confidence_score DECIMAL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_datasets_source ON datasets(source);
CREATE INDEX IF NOT EXISTS idx_datasets_name ON datasets(name);
CREATE INDEX IF NOT EXISTS idx_datasets_active ON datasets(is_active);

CREATE INDEX IF NOT EXISTS idx_samples_dataset_id ON samples(dataset_id);
CREATE INDEX IF NOT EXISTS idx_samples_sample_id ON samples(sample_id);
CREATE INDEX IF NOT EXISTS idx_samples_sample_type ON samples(sample_type);
CREATE INDEX IF NOT EXISTS idx_samples_disease_type ON samples(disease_type);

CREATE INDEX IF NOT EXISTS idx_variants_dataset_id ON variants(dataset_id);
CREATE INDEX IF NOT EXISTS idx_variants_chromosome_position ON variants(chromosome, position);
CREATE INDEX IF NOT EXISTS idx_variants_variant_type ON variants(variant_type);
CREATE INDEX IF NOT EXISTS idx_variants_clinical_significance ON variants(clinical_significance);

CREATE INDEX IF NOT EXISTS idx_gene_expression_dataset_id ON gene_expression(dataset_id);
CREATE INDEX IF NOT EXISTS idx_gene_expression_sample_id ON gene_expression(sample_id);
CREATE INDEX IF NOT EXISTS idx_gene_expression_gene_id ON gene_expression(gene_id);
CREATE INDEX IF NOT EXISTS idx_gene_expression_gene_name ON gene_expression(gene_name);

CREATE INDEX IF NOT EXISTS idx_drug_targets_drug_id ON drug_targets(drug_id);
CREATE INDEX IF NOT EXISTS idx_drug_targets_target_gene ON drug_targets(target_gene);
CREATE INDEX IF NOT EXISTS idx_drug_targets_source ON drug_targets(source);

CREATE INDEX IF NOT EXISTS idx_literature_entities_pmid ON literature_entities(pmid);
CREATE INDEX IF NOT EXISTS idx_literature_entities_entity_type ON literature_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_literature_entities_entity_name ON literature_entities(entity_name);
CREATE INDEX IF NOT EXISTS idx_literature_entities_source ON literature_entities(source);

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_user_id ON analysis_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_job_type ON analysis_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_created_at ON analysis_jobs(created_at);

CREATE INDEX IF NOT EXISTS idx_model_predictions_analysis_job_id ON model_predictions(analysis_job_id);
CREATE INDEX IF NOT EXISTS idx_model_predictions_model_type ON model_predictions(model_type);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_datasets_updated_at BEFORE UPDATE ON datasets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some initial data for testing
INSERT INTO datasets (name, source, description, version, total_samples, total_variants, is_active) VALUES
('TCGA Breast Cancer', 'TCGA', 'The Cancer Genome Atlas Breast Cancer dataset', '1.0', 1000, 5000000, true),
('ClinVar Variants', 'CLINVAR', 'Clinical variant database with pathogenicity annotations', '1.0', 0, 1000000, true),
('PubMed Genomics Literature', 'PUBMED', 'Biomedical literature for genomics research', '1.0', 0, 0, true)
ON CONFLICT DO NOTHING;

-- Grant permissions to the genomics_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO genomics_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO genomics_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO genomics_user;

-- Create a view for dataset summary
CREATE OR REPLACE VIEW dataset_summary AS
SELECT 
    d.id,
    d.name,
    d.source,
    d.description,
    d.version,
    d.total_samples,
    d.total_variants,
    d.created_at,
    d.updated_at,
    d.is_active,
    COUNT(DISTINCT s.id) as actual_samples,
    COUNT(DISTINCT v.id) as actual_variants
FROM datasets d
LEFT JOIN samples s ON d.id = s.dataset_id
LEFT JOIN variants v ON d.id = v.dataset_id
GROUP BY d.id, d.name, d.source, d.description, d.version, d.total_samples, d.total_variants, d.created_at, d.updated_at, d.is_active;

-- Grant access to the view
GRANT SELECT ON dataset_summary TO genomics_user; 