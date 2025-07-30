#!/usr/bin/env python3
"""
Variant Pathogenicity Predictor

ML model for predicting variant pathogenicity using ClinVar and gnomAD data.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from typing import Dict, List, Optional, Union, Tuple
import logging
import json
from pathlib import Path

from .base_model import BaseModel

logger = logging.getLogger(__name__)

class VariantPredictor(BaseModel):
    """Variant pathogenicity prediction model."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the variant predictor.
        
        Args:
            model_path: Path to saved model
        """
        super().__init__(model_path, model_name="variant_predictor")
        
        # Initialize models
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.gb_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=42
        )
        
        # Preprocessing
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Feature names
        self.feature_names = [
            'chromosome', 'position', 'ref_allele_length', 'alt_allele_length',
            'allele_frequency', 'quality_score', 'depth', 'strand_bias',
            'gene_density', 'conservation_score', 'gc_content'
        ]
    
    def _extract_features(self, variants_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from variant data.
        
        Args:
            variants_df: DataFrame with variant information
            
        Returns:
            DataFrame with extracted features
        """
        features = pd.DataFrame()
        
        # Basic variant features
        features['chromosome'] = variants_df['chromosome'].astype('category').cat.codes
        features['position'] = variants_df['position']
        
        # Allele features
        features['ref_allele_length'] = variants_df['reference_allele'].str.len()
        features['alt_allele_length'] = variants_df['alternate_allele'].str.len()
        
        # Frequency and quality
        features['allele_frequency'] = variants_df['allele_frequency'].fillna(0)
        features['quality_score'] = variants_df['quality_score'].fillna(50)
        
        # Additional features (simulated for demo)
        features['depth'] = np.random.randint(10, 1000, len(variants_df))
        features['strand_bias'] = np.random.uniform(0, 1, len(variants_df))
        features['gene_density'] = np.random.uniform(0, 1, len(variants_df))
        features['conservation_score'] = np.random.uniform(0, 1, len(variants_df))
        features['gc_content'] = np.random.uniform(0.3, 0.7, len(variants_df))
        
        return features
    
    def _prepare_labels(self, variants_df: pd.DataFrame) -> np.ndarray:
        """
        Prepare labels for training.
        
        Args:
            variants_df: DataFrame with variant information
            
        Returns:
            Array of labels (1 for pathogenic, 0 for benign)
        """
        # Map clinical significance to binary labels
        pathogenic_terms = ['pathogenic', 'likely_pathogenic']
        benign_terms = ['benign', 'likely_benign']
        
        labels = []
        for significance in variants_df['clinical_significance']:
            if significance in pathogenic_terms:
                labels.append(1)
            elif significance in benign_terms:
                labels.append(0)
            else:
                labels.append(-1)  # VUS, will be filtered out
        
        return np.array(labels)
    
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series], 
              model_type: str = 'random_forest', **kwargs) -> Dict[str, float]:
        """
        Train the variant predictor.
        
        Args:
            X: Training features
            y: Training labels
            model_type: Type of model ('random_forest' or 'gradient_boosting')
            **kwargs: Additional parameters
            
        Returns:
            Dictionary of training metrics
        """
        logger.info(f"Training variant predictor with {model_type}")
        
        # Prepare data
        if isinstance(X, pd.DataFrame):
            X_features = self._extract_features(X)
            y_labels = self._prepare_labels(X)
        else:
            X_features = X
            y_labels = y
        
        # Filter out VUS (uncertain significance)
        valid_mask = y_labels != -1
        X_filtered = X_features[valid_mask]
        y_filtered = y_labels[valid_mask]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_filtered, y_filtered, test_size=0.2, random_state=42, stratify=y_filtered
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        if model_type == 'random_forest':
            self.model = self.rf_model
        elif model_type == 'gradient_boosting':
            self.model = self.gb_model
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba)
        }
        
        self.is_trained = True
        self.metrics = metrics
        
        logger.info(f"Training completed. ROC-AUC: {metrics['roc_auc']:.3f}")
        return metrics
    
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> Union[np.ndarray, List[float]]:
        """
        Predict variant pathogenicity.
        
        Args:
            X: Input variants
            
        Returns:
            Array of pathogenicity scores (0-1)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Prepare features
        if isinstance(X, pd.DataFrame):
            X_features = self._extract_features(X)
        else:
            X_features = X
        
        # Scale features
        X_scaled = self.scaler.transform(X_features)
        
        # Make predictions
        predictions = self.model.predict_proba(X_scaled)[:, 1]
        
        return predictions
    
    def predict_clinical_significance(self, X: Union[np.ndarray, pd.DataFrame]) -> List[str]:
        """
        Predict clinical significance categories.
        
        Args:
            X: Input variants
            
        Returns:
            List of clinical significance predictions
        """
        scores = self.predict(X)
        
        significance = []
        for score in scores:
            if score > 0.8:
                significance.append('Pathogenic')
            elif score > 0.6:
                significance.append('Likely Pathogenic')
            elif score > 0.4:
                significance.append('VUS')
            elif score > 0.2:
                significance.append('Likely Benign')
            else:
                significance.append('Benign')
        
        return significance
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if not self.is_trained:
            return {}
        
        importance = self.model.feature_importances_
        return dict(zip(self.feature_names, importance))
    
    def save_model(self, path: str) -> None:
        """Save the trained model with all components."""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save main model
            joblib.dump(self.model, f"{path}_model.joblib")
            
            # Save preprocessing components
            joblib.dump(self.scaler, f"{path}_scaler.joblib")
            joblib.dump(self.label_encoder, f"{path}_encoder.joblib")
            
            # Save metadata
            metadata = {
                "model_name": self.model_name,
                "is_trained": self.is_trained,
                "metrics": self.metrics,
                "feature_names": self.feature_names
            }
            
            with open(f"{path}_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Variant predictor saved to {path}")
            
        except Exception as e:
            logger.error(f"Failed to save variant predictor: {e}")
            raise
    
    def load_model(self) -> None:
        """Load the trained model with all components."""
        try:
            if not self.model_path:
                raise ValueError("No model path specified")
            
            # Load main model
            self.model = joblib.load(f"{self.model_path}_model.joblib")
            
            # Load preprocessing components
            self.scaler = joblib.load(f"{self.model_path}_scaler.joblib")
            self.label_encoder = joblib.load(f"{self.model_path}_encoder.joblib")
            
            # Load metadata
            metadata_path = f"{self.model_path}_metadata.json"
            if Path(metadata_path).exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.is_trained = metadata.get("is_trained", False)
                    self.metrics = metadata.get("metrics", {})
                    self.feature_names = metadata.get("feature_names", [])
            
            logger.info(f"Variant predictor loaded from {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load variant predictor: {e}")
            raise 