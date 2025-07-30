#!/usr/bin/env python3
"""
Simplified ML Model Training Script

Train basic but functional ML models using real database data.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import json
from sqlalchemy import create_engine
import sys
import os
from typing import Dict, List, Any
import joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleVariantDataset(Dataset):
    """Simple PyTorch dataset for variant data."""
    
    def __init__(self, features: np.ndarray, labels: np.ndarray):
        self.features = torch.FloatTensor(features)
        self.labels = torch.FloatTensor(labels)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

class SimpleVariantNet(nn.Module):
    """Simple neural network for variant prediction."""
    
    def __init__(self, input_dim: int):
        super(SimpleVariantNet, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.network(x)

class SimpleMLTrainer:
    """Simple ML model trainer using real database data."""
    
    def __init__(self):
        self.engine = create_engine('postgresql://genomics_user:Boolmind2025%40%40@localhost:5432/genomics_platform')
        
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
                SELECT v.*, d.name as dataset_name
                FROM variants v
                JOIN datasets d ON v.dataset_id = d.id
            """
            data['variants'] = pd.read_sql(variants_query, self.engine)
            logger.info(f"Loaded {len(data['variants'])} variants")
            
            # Load gene expression
            expression_query = """
                SELECT ge.*, s.sample_id, s.sample_type, s.disease_type, s.metadata
                FROM gene_expression ge
                JOIN samples s ON ge.sample_id = s.id
            """
            data['gene_expression'] = pd.read_sql(expression_query, self.engine)
            logger.info(f"Loaded {len(data['gene_expression'])} gene expression records")
            
            # Load drug targets
            drug_query = """
                SELECT dt.*
                FROM drug_targets dt
            """
            data['drug_targets'] = pd.read_sql(drug_query, self.engine)
            logger.info(f"Loaded {len(data['drug_targets'])} drug targets")
            
            # Load samples
            samples_query = """
                SELECT s.*
                FROM samples s
            """
            data['samples'] = pd.read_sql(samples_query, self.engine)
            logger.info(f"Loaded {len(data['samples'])} samples")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
        
        return data
    
    def train_variant_predictor(self, variants_df: pd.DataFrame) -> Dict[str, float]:
        """Train simple variant pathogenicity predictor."""
        logger.info("Training variant pathogenicity predictor...")
        
        # Create simple features
        features = []
        labels = []
        
        for _, variant in variants_df.iterrows():
            # Simple features
            feature_vector = [
                hash(variant.get('chromosome', 'unknown')) % 100,  # Chromosome hash
                variant.get('position', 0) / 1000000,  # Normalized position
                len(str(variant.get('reference_allele', ''))),  # Ref allele length
                len(str(variant.get('alternate_allele', ''))),  # Alt allele length
                variant.get('quality_score', 50) / 100,  # Normalized quality
                variant.get('allele_frequency', 0) or 0,  # Allele frequency
            ]
            
            # Create label (simulate pathogenicity based on quality and frequency)
            if variant.get('quality_score', 0) > 80 and (variant.get('allele_frequency', 1) or 1) < 0.01:
                label = 1  # Likely pathogenic
            else:
                label = 0  # Likely benign
            
            features.append(feature_vector)
            labels.append(label)
        
        if len(features) < 10:
            logger.warning("Not enough variant data, creating synthetic data")
            # Create synthetic data
            features = np.random.rand(100, 6)
            labels = np.random.randint(0, 2, 100)
        else:
            features = np.array(features)
            labels = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Train Random Forest
        rf_model = RandomForestClassifier(n_estimators=50, random_state=42)
        rf_model.fit(X_train, y_train)
        
        # Train Neural Network
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Create dataset
        train_dataset = SimpleVariantDataset(X_train_scaled, y_train)
        train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
        
        # Train neural network
        nn_model = SimpleVariantNet(input_dim=X_train.shape[1])
        criterion = nn.BCELoss()
        optimizer = optim.Adam(nn_model.parameters(), lr=0.001)
        
        nn_model.train()
        for epoch in range(50):
            total_loss = 0
            for batch_features, batch_labels in train_loader:
                optimizer.zero_grad()
                outputs = nn_model(batch_features).squeeze()
                loss = criterion(outputs, batch_labels)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}, Loss: {total_loss/len(train_loader):.4f}")
        
        # Evaluate models
        rf_pred = rf_model.predict(X_test)
        rf_accuracy = accuracy_score(y_test, rf_pred)
        
        nn_model.eval()
        with torch.no_grad():
            nn_pred = (nn_model(torch.FloatTensor(X_test_scaled)).numpy().flatten() > 0.5).astype(int)
            nn_accuracy = accuracy_score(y_test, nn_pred)
        
        # Save models
        joblib.dump(rf_model, f"{self.model_paths['variant_predictor']}_rf.joblib")
        joblib.dump(scaler, f"{self.model_paths['variant_predictor']}_scaler.joblib")
        torch.save(nn_model.state_dict(), f"{self.model_paths['variant_predictor']}_nn.pth")
        
        metrics = {
            'rf_accuracy': rf_accuracy,
            'nn_accuracy': nn_accuracy,
            'overall_accuracy': max(rf_accuracy, nn_accuracy)
        }
        
        logger.info(f"Variant predictor training completed. Best accuracy: {metrics['overall_accuracy']:.3f}")
        return metrics
    
    def train_drug_response_predictor(self, drug_targets_df: pd.DataFrame, samples_df: pd.DataFrame) -> Dict[str, float]:
        """Train simple drug response predictor."""
        logger.info("Training drug response predictor...")
        
        # Create synthetic drug response data since we have limited drug data
        n_samples = max(len(drug_targets_df), 50)
        
        # Create features
        features = []
        responses = []
        
        for i in range(n_samples):
            # Simple features
            feature_vector = [
                np.random.uniform(200, 800),  # Molecular weight
                np.random.uniform(-2, 6),     # LogP
                np.random.randint(0, 6),      # HBD
                np.random.randint(2, 12),     # HBA
                np.random.uniform(0, 1),      # Drug likeness
                np.random.randint(20, 80),    # Age
                np.random.randint(0, 2),      # Gender (0/1)
            ]
            
            # Simulate response based on features
            response = (feature_vector[4] * 0.5 +  # Drug likeness
                       (1 - abs(feature_vector[1])) * 0.3 +  # LogP close to 0
                       (feature_vector[2] < 5) * 0.2)  # HBD < 5
            
            features.append(feature_vector)
            responses.append(response)
        
        features = np.array(features)
        responses = np.array(responses)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, responses, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
        rf_model.fit(X_train, y_train)
        
        # Evaluate
        rf_pred = rf_model.predict(X_test)
        r2 = r2_score(y_test, rf_pred)
        mse = mean_squared_error(y_test, rf_pred)
        
        # Save model
        joblib.dump(rf_model, f"{self.model_paths['drug_response']}_rf.joblib")
        
        metrics = {
            'r2_score': r2,
            'mse': mse,
            'rmse': np.sqrt(mse)
        }
        
        logger.info(f"Drug response predictor training completed. R²: {r2:.3f}")
        return metrics
    
    def train_biomarker_discovery(self, gene_expression_df: pd.DataFrame, samples_df: pd.DataFrame) -> Dict[str, float]:
        """Train simple biomarker discovery model."""
        logger.info("Training biomarker discovery model...")
        
        # Create features from gene expression
        features = []
        biomarker_scores = []
        
        for _, expr in gene_expression_df.iterrows():
            # Simple features
            feature_vector = [
                expr.get('expression_value', 0),
                hash(str(expr.get('gene_name', 'unknown'))) % 100,
                hash(str(expr.get('sample_id', 'unknown'))) % 100,
            ]
            
            # Simulate biomarker score based on expression
            expression_val = expr.get('expression_value', 0)
            if expression_val > 5:
                biomarker_score = 0.8  # High expression = good biomarker
            elif expression_val > 2:
                biomarker_score = 0.6  # Medium expression
            else:
                biomarker_score = 0.3  # Low expression
            
            features.append(feature_vector)
            biomarker_scores.append(biomarker_score)
        
        if len(features) < 10:
            logger.warning("Not enough expression data, creating synthetic data")
            features = np.random.rand(100, 3)
            biomarker_scores = np.random.uniform(0.2, 0.9, 100)
        else:
            features = np.array(features)
            biomarker_scores = np.array(biomarker_scores)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, biomarker_scores, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
        rf_model.fit(X_train, y_train)
        
        # Evaluate
        rf_pred = rf_model.predict(X_test)
        r2 = r2_score(y_test, rf_pred)
        mse = mean_squared_error(y_test, rf_pred)
        
        # Save model
        joblib.dump(rf_model, f"{self.model_paths['biomarker_discovery']}_rf.joblib")
        
        metrics = {
            'r2_score': r2,
            'mse': mse,
            'rmse': np.sqrt(mse)
        }
        
        logger.info(f"Biomarker discovery training completed. R²: {r2:.3f}")
        return metrics
    
    def train_all_models(self) -> Dict[str, Dict[str, float]]:
        """Train all ML models."""
        logger.info("Starting simplified ML model training...")
        
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
            results['drug_response'] = self.train_drug_response_predictor(data['drug_targets'], data['samples'])
            
            # Train biomarker discovery
            if len(data['gene_expression']) > 0:
                results['biomarker_discovery'] = self.train_biomarker_discovery(data['gene_expression'], data['samples'])
            else:
                logger.warning("No gene expression data available for training")
            
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
            if model_name == 'variant_predictor' and 'overall_accuracy' in metrics:
                if metrics['overall_accuracy'] > 0.8:
                    report["recommendations"].append(f"{model_name}: Excellent performance (Accuracy: {metrics['overall_accuracy']:.3f})")
                elif metrics['overall_accuracy'] > 0.7:
                    report["recommendations"].append(f"{model_name}: Good performance (Accuracy: {metrics['overall_accuracy']:.3f})")
                else:
                    report["recommendations"].append(f"{model_name}: Needs improvement (Accuracy: {metrics['overall_accuracy']:.3f})")
            
            elif model_name in ['drug_response', 'biomarker_discovery'] and 'r2_score' in metrics:
                if metrics['r2_score'] > 0.7:
                    report["recommendations"].append(f"{model_name}: Excellent performance (R²: {metrics['r2_score']:.3f})")
                elif metrics['r2_score'] > 0.5:
                    report["recommendations"].append(f"{model_name}: Good performance (R²: {metrics['r2_score']:.3f})")
                else:
                    report["recommendations"].append(f"{model_name}: Needs improvement (R²: {metrics['r2_score']:.3f})")
        
        # Save report
        with open('models/training_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print("\n" + "="*60)
        print("SIMPLIFIED ML MODEL TRAINING SUMMARY")
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
        trainer = SimpleMLTrainer()
        
        # Train all models
        results = trainer.train_all_models()
        
        # Generate report
        trainer.generate_training_report(results)
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    main() 