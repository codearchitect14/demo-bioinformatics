#!/usr/bin/env python3
"""
Train Variant Predictor Model

Script to train the variant pathogenicity prediction model.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.variant_predictor import VariantPredictor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    Create sample variant data for training.
    
    Args:
        n_samples: Number of samples to create
        
    Returns:
        DataFrame with sample variant data
    """
    logger.info(f"Creating sample data with {n_samples} variants")
    
    # Sample chromosomes
    chromosomes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 
                  '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', 'X', 'Y']
    
    # Sample alleles
    ref_alleles = ['A', 'T', 'G', 'C']
    alt_alleles = ['A', 'T', 'G', 'C']
    
    # Clinical significance options
    significance_options = ['pathogenic', 'likely_pathogenic', 'benign', 'likely_benign', 'uncertain_significance']
    
    data = []
    for i in range(n_samples):
        # Create variant
        chromosome = np.random.choice(chromosomes)
        position = np.random.randint(1, 250000000)
        
        ref_allele = np.random.choice(ref_alleles)
        alt_allele = np.random.choice([a for a in alt_alleles if a != ref_allele])
        
        # Clinical significance (biased towards pathogenic for demo)
        significance = np.random.choice(significance_options, p=[0.3, 0.2, 0.2, 0.2, 0.1])
        
        # Quality metrics
        quality_score = np.random.uniform(20, 100)
        allele_frequency = np.random.uniform(0, 0.5)
        
        data.append({
            'id': f'var_{i:06d}',
            'chromosome': chromosome,
            'position': position,
            'reference_allele': ref_allele,
            'alternate_allele': alt_allele,
            'clinical_significance': significance,
            'quality_score': quality_score,
            'allele_frequency': allele_frequency,
            'gene': f'GENE_{np.random.randint(1, 1000):03d}',
            'variant_type': np.random.choice(['SNV', 'INDEL', 'CNV'])
        })
    
    return pd.DataFrame(data)

def main():
    """Main training function."""
    logger.info("Starting variant predictor training")
    
    # Create sample data
    variants_df = create_sample_data(n_samples=2000)
    logger.info(f"Created {len(variants_df)} sample variants")
    
    # Initialize model
    model = VariantPredictor()
    
    # Train model
    logger.info("Training variant predictor...")
    metrics = model.train(variants_df, variants_df, model_type='random_forest')
    
    # Print results
    logger.info("Training completed!")
    logger.info("Metrics:")
    for metric, value in metrics.items():
        logger.info(f"  {metric}: {value:.3f}")
    
    # Save model
    model_path = "models/variant_predictor"
    model.save_model(model_path)
    logger.info(f"Model saved to {model_path}")
    
    # Test prediction
    logger.info("Testing prediction...")
    test_variants = variants_df.head(5)
    predictions = model.predict(test_variants)
    significance = model.predict_clinical_significance(test_variants)
    
    logger.info("Sample predictions:")
    for i, (_, variant) in enumerate(test_variants.iterrows()):
        logger.info(f"  Variant {variant['id']}: {variant['gene']} - "
                   f"Score: {predictions[i]:.3f}, Significance: {significance[i]}")
    
    # Feature importance
    importance = model.get_feature_importance()
    logger.info("Top 5 feature importance:")
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    for feature, score in sorted_importance[:5]:
        logger.info(f"  {feature}: {score:.3f}")
    
    logger.info("Training completed successfully!")

if __name__ == "__main__":
    main() 