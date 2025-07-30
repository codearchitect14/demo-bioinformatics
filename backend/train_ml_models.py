#!/usr/bin/env python3
"""
Comprehensive ML Model Training Script

Train all state-of-the-art ML models using real database data.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os
from typing import Dict, List, Any

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.ml.variant_predictor import VariantPathogenicityPredictor
from app.ml.drug_response_predictor import DrugResponsePredictor
from app.ml.biomarker_discovery import BiomarkerDiscoveryModel

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MLModelTrainer:
    """Comprehensive ML model trainer using real database data."""
    
    def __init__(self):
        self.engine = create_engine('postgresql://genomics_user:Boolmind2025%40%40@localhost:5432/genomics_platform')
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Model paths
        self.model_paths = {
            'variant_predictor': 'models/variant_predictor',
            'drug_response': 'models/drug_response',
            'biomarker_discovery': 'models/biomarker_discovery'
        }
        
        # Create models directory
        Path('models').mkdir(exist_ok=True)
    
    def load_database_data(self) -> Dict[str, pd.DataFrame]:
        """Load all data from database."""
        logger.info("Loading data from database...")
        
        data = {}
        
        try:
            # Load variants
            variants_query = """
                SELECT v.*, d.name as dataset_name, d.source as dataset_source
                FROM variants v
                JOIN datasets d ON v.dataset_id = d.id
                WHERE v.clinical_significance IS NOT NULL
                AND v.clinical_significance != ''
            """
            data['variants'] = pd.read_sql(variants_query, self.engine)
            logger.info(f"Loaded {len(data['variants'])} variants")
            
            # Load gene expression
            expression_query = """
                SELECT ge.*, s.sample_id, s.sample_type, s.disease_type, s.metadata,
                       d.name as dataset_name
                FROM gene_expression ge
                JOIN samples s ON ge.sample_id = s.id
                JOIN datasets d ON ge.dataset_id = d.id
            """
            data['gene_expression'] = pd.read_sql(expression_query, self.engine)
            logger.info(f"Loaded {len(data['gene_expression'])} gene expression records")
            
            # Load drug targets
            drug_query = """
                SELECT dt.*, d.name as dataset_name
                FROM drug_targets dt
                JOIN datasets d ON dt.source = d.source
            """
            data['drug_targets'] = pd.read_sql(drug_query, self.engine)
            logger.info(f"Loaded {len(data['drug_targets'])} drug targets")
            
            # Load samples
            samples_query = """
                SELECT s.*, d.name as dataset_name
                FROM samples s
                JOIN datasets d ON s.dataset_id = d.id
            """
            data['samples'] = pd.read_sql(samples_query, self.engine)
            logger.info(f"Loaded {len(data['samples'])} samples")
            
            # Load literature entities
            literature_query = """
                SELECT le.*, d.name as dataset_name
                FROM literature_entities le
                JOIN datasets d ON le.source = d.source
            """
            data['literature_entities'] = pd.read_sql(literature_query, self.engine)
            logger.info(f"Loaded {len(data['literature_entities'])} literature entities")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
        
        return data
    
    def train_variant_predictor(self, variants_df: pd.DataFrame) -> Dict[str, float]:
        """Train variant pathogenicity predictor."""
        logger.info("Training variant pathogenicity predictor...")
        
        # Filter variants with clinical significance
        valid_variants = variants_df[
            variants_df['clinical_significance'].isin([
                'pathogenic', 'likely_pathogenic', 'benign', 'likely_benign'
            ])
        ].copy()
        
        if len(valid_variants) < 100:
            logger.warning(f"Only {len(valid_variants)} variants with clinical significance. Using all variants.")
            valid_variants = variants_df.copy()
        
        # Initialize and train model
        model = VariantPathogenicityPredictor()
        metrics = model.train(valid_variants, validation_split=0.2)
        
        # Save model
        model.save_model(self.model_paths['variant_predictor'])
        
        logger.info(f"Variant predictor training completed. ROC-AUC: {metrics['roc_auc']:.3f}")
        return metrics
    
    def train_drug_response_predictor(self, drug_targets_df: pd.DataFrame, samples_df: pd.DataFrame) -> Dict[str, float]:
        """Train drug response predictor."""
        logger.info("Training drug response predictor...")
        
        # Filter data
        valid_drugs = drug_targets_df[drug_targets_df['binding_affinity'].notna()].copy()
        valid_samples = samples_df[samples_df['metadata'].notna()].copy()
        
        if len(valid_drugs) < 10 or len(valid_samples) < 10:
            logger.warning("Insufficient drug or sample data. Using all data.")
            valid_drugs = drug_targets_df.copy()
            valid_samples = samples_df.copy()
        
        # Initialize and train model
        model = DrugResponsePredictor()
        metrics = model.train(valid_drugs, valid_samples, validation_split=0.2)
        
        # Save model
        model.save_model(self.model_paths['drug_response'])
        
        logger.info(f"Drug response predictor training completed. R² Score: {metrics['r2_score']:.3f}")
        return metrics
    
    def train_biomarker_discovery(self, gene_expression_df: pd.DataFrame, samples_df: pd.DataFrame) -> Dict[str, float]:
        """Train biomarker discovery model."""
        logger.info("Training biomarker discovery model...")
        
        # Filter data
        valid_expression = gene_expression_df[gene_expression_df['expression_value'].notna()].copy()
        valid_samples = samples_df[samples_df['metadata'].notna()].copy()
        
        if len(valid_expression) < 10 or len(valid_samples) < 10:
            logger.warning("Insufficient expression or sample data. Using all data.")
            valid_expression = gene_expression_df.copy()
            valid_samples = samples_df.copy()
        
        # Initialize and train model
        model = BiomarkerDiscoveryModel()
        metrics = model.train(valid_expression, valid_samples, validation_split=0.2)
        
        # Save model
        model.save_model(self.model_paths['biomarker_discovery'])
        
        logger.info(f"Biomarker discovery training completed. C-index: {metrics['c_index']:.3f}")
        return metrics
    
    def train_all_models(self) -> Dict[str, Dict[str, float]]:
        """Train all ML models."""
        logger.info("Starting comprehensive ML model training...")
        
        # Load data
        data = self.load_database_data()
        
        # Training results
        results = {}
        
        try:
            # Train variant predictor
            if len(data['variants']) > 0:
                results['variant_predictor'] = self.train_variant_predictor(data['variants'])
            else:
                logger.warning("No variant data available for training")
            
            # Train drug response predictor
            if len(data['drug_targets']) > 0 and len(data['samples']) > 0:
                results['drug_response'] = self.train_drug_response_predictor(data['drug_targets'], data['samples'])
            else:
                logger.warning("Insufficient drug or sample data for training")
            
            # Train biomarker discovery
            if len(data['gene_expression']) > 0 and len(data['samples']) > 0:
                results['biomarker_discovery'] = self.train_biomarker_discovery(data['gene_expression'], data['samples'])
            else:
                logger.warning("Insufficient expression or sample data for training")
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
            raise
        
        # Save training results
        with open('models/training_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("All model training completed!")
        return results
    
    def generate_training_report(self, results: Dict[str, Dict[str, float]]):
        """Generate comprehensive training report."""
        logger.info("Generating training report...")
        
        report = {
            "training_summary": {
                "total_models_trained": len(results),
                "models": list(results.keys()),
                "timestamp": pd.Timestamp.now().isoformat()
            },
            "model_performance": results,
            "recommendations": []
        }
        
        # Add recommendations based on performance
        for model_name, metrics in results.items():
            if model_name == 'variant_predictor' and 'roc_auc' in metrics:
                if metrics['roc_auc'] > 0.85:
                    report["recommendations"].append(f"{model_name}: Excellent performance (ROC-AUC: {metrics['roc_auc']:.3f})")
                elif metrics['roc_auc'] > 0.75:
                    report["recommendations"].append(f"{model_name}: Good performance (ROC-AUC: {metrics['roc_auc']:.3f})")
                else:
                    report["recommendations"].append(f"{model_name}: Needs improvement (ROC-AUC: {metrics['roc_auc']:.3f})")
            
            elif model_name == 'drug_response' and 'r2_score' in metrics:
                if metrics['r2_score'] > 0.7:
                    report["recommendations"].append(f"{model_name}: Excellent performance (R²: {metrics['r2_score']:.3f})")
                elif metrics['r2_score'] > 0.5:
                    report["recommendations"].append(f"{model_name}: Good performance (R²: {metrics['r2_score']:.3f})")
                else:
                    report["recommendations"].append(f"{model_name}: Needs improvement (R²: {metrics['r2_score']:.3f})")
            
            elif model_name == 'biomarker_discovery' and 'c_index' in metrics:
                if metrics['c_index'] > 0.7:
                    report["recommendations"].append(f"{model_name}: Excellent performance (C-index: {metrics['c_index']:.3f})")
                elif metrics['c_index'] > 0.6:
                    report["recommendations"].append(f"{model_name}: Good performance (C-index: {metrics['c_index']:.3f})")
                else:
                    report["recommendations"].append(f"{model_name}: Needs improvement (C-index: {metrics['c_index']:.3f})")
        
        # Save report
        with open('models/training_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*60)
        print("ML MODEL TRAINING SUMMARY")
        print("="*60)
        print(f"Models trained: {len(results)}")
        print(f"Timestamp: {report['training_summary']['timestamp']}")
        print("\nPerformance Metrics:")
        
        for model_name, metrics in results.items():
            print(f"\n{model_name.upper()}:")
            for metric, value in metrics.items():
                print(f"  {metric}: {value:.3f}")
        
        print("\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
        
        print("\n" + "="*60)
        print("Training completed! Models saved to 'models/' directory")
        print("="*60)

def main():
    """Main training function."""
    try:
        # Initialize trainer
        trainer = MLModelTrainer()
        
        # Train all models
        results = trainer.train_all_models()
        
        # Generate report
        trainer.generate_training_report(results)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    main() 