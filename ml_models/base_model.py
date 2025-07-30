#!/usr/bin/env python3
"""
Base Model Class

Abstract base class for all ML models in the genomics platform.
"""

from abc import ABC, abstractmethod
import joblib
import torch
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """Abstract base class for all ML models."""
    
    def __init__(self, model_path: Optional[str] = None, model_name: str = "base_model"):
        """
        Initialize the base model.
        
        Args:
            model_path: Path to saved model file
            model_name: Name of the model for logging
        """
        self.model = None
        self.model_path = model_path
        self.model_name = model_name
        self.is_trained = False
        self.metrics = {}
        
        if model_path and Path(model_path).exists():
            self.load_model()
    
    @abstractmethod
    def train(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series], **kwargs) -> Dict[str, float]:
        """
        Train the model.
        
        Args:
            X: Training features
            y: Training labels
            **kwargs: Additional training parameters
            
        Returns:
            Dictionary of training metrics
        """
        pass
    
    @abstractmethod
    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> Union[np.ndarray, List[float]]:
        """
        Make predictions.
        
        Args:
            X: Input features
            
        Returns:
            Predictions
        """
        pass
    
    def save_model(self, path: str) -> None:
        """
        Save the trained model.
        
        Args:
            path: Path to save the model
        """
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            if hasattr(self.model, 'save_pretrained'):
                # For transformers models
                self.model.save_pretrained(path)
            else:
                # For scikit-learn and other models
                joblib.dump(self.model, f"{path}.joblib")
            
            # Save metadata
            metadata = {
                "model_name": self.model_name,
                "is_trained": self.is_trained,
                "metrics": self.metrics
            }
            
            with open(f"{path}_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Model saved to {path}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise
    
    def load_model(self) -> None:
        """Load the trained model."""
        try:
            if not self.model_path:
                raise ValueError("No model path specified")
            
            model_file = Path(self.model_path)
            
            if model_file.is_dir():
                # For transformers models
                from transformers import AutoModel, AutoTokenizer
                self.model = AutoModel.from_pretrained(str(model_file))
                self.tokenizer = AutoTokenizer.from_pretrained(str(model_file))
            else:
                # For scikit-learn and other models
                self.model = joblib.load(f"{self.model_path}.joblib")
            
            # Load metadata
            metadata_path = f"{self.model_path}_metadata.json"
            if Path(metadata_path).exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.is_trained = metadata.get("is_trained", False)
                    self.metrics = metadata.get("metrics", {})
            
            logger.info(f"Model loaded from {self.model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def evaluate(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> Dict[str, float]:
        """
        Evaluate the model performance.
        
        Args:
            X: Test features
            y: Test labels
            
        Returns:
            Dictionary of evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        
        predictions = self.predict(X)
        
        # Convert to numpy arrays
        y_true = np.array(y)
        y_pred = np.array(predictions)
        
        # Calculate metrics
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, average='weighted'),
            "recall": recall_score(y_true, y_pred, average='weighted'),
            "f1_score": f1_score(y_true, y_pred, average='weighted')
        }
        
        # Add ROC-AUC if binary classification
        if len(np.unique(y_true)) == 2:
            try:
                metrics["roc_auc"] = roc_auc_score(y_true, y_pred)
            except:
                pass
        
        self.metrics.update(metrics)
        return metrics
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance if available.
        
        Returns:
            Dictionary of feature importance scores
        """
        if not self.is_trained:
            return None
        
        if hasattr(self.model, 'feature_importances_'):
            return dict(zip(self.feature_names, self.model.feature_importances_))
        elif hasattr(self.model, 'coef_'):
            return dict(zip(self.feature_names, self.model.coef_))
        else:
            return None
    
    def __repr__(self):
        return f"{self.__class__.__name__}(model_name='{self.model_name}', is_trained={self.is_trained})" 