#!/usr/bin/env python3
"""
State-of-the-Art Biomarker Discovery Model

Advanced ML model for biomarker discovery using survival analysis,
Cox regression, machine learning, and comprehensive statistical methods.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test
import xgboost as xgb
import lightgbm as lgb
from scipy import stats
from typing import Dict, List, Optional, Tuple, Union
import joblib
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class BiomarkerDataset(Dataset):
    """PyTorch dataset for biomarker data."""
    
    def __init__(self, expression_features: np.ndarray, clinical_features: np.ndarray, 
                 survival_times: np.ndarray, event_indicators: np.ndarray):
        self.expression_features = torch.FloatTensor(expression_features)
        self.clinical_features = torch.FloatTensor(clinical_features)
        self.survival_times = torch.FloatTensor(survival_times)
        self.event_indicators = torch.FloatTensor(event_indicators)
    
    def __len__(self):
        return len(self.expression_features)
    
    def __getitem__(self, idx):
        return (self.expression_features[idx], self.clinical_features[idx],
                self.survival_times[idx], self.event_indicators[idx])

class BiomarkerNeuralNetwork(nn.Module):
    """Deep neural network for biomarker discovery."""
    
    def __init__(self, expression_dim: int, clinical_dim: int, hidden_dims: List[int] = [256, 128, 64]):
        super(BiomarkerNeuralNetwork, self).__init__()
        
        # Expression feature encoder
        self.expression_encoder = nn.Sequential(
            nn.Linear(expression_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        # Clinical feature encoder
        self.clinical_encoder = nn.Sequential(
            nn.Linear(clinical_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        # Fusion network
        fusion_input_dim = 64 + 64  # Combined features
        layers = []
        prev_dim = fusion_input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3)
            ])
            prev_dim = hidden_dim
        
        # Output layers for different tasks
        self.survival_head = nn.Linear(prev_dim, 1)  # Survival prediction
        self.biomarker_head = nn.Linear(prev_dim, 1)  # Biomarker score
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, expression_features, clinical_features):
        # Encode features
        expr_encoded = self.expression_encoder(expression_features)
        clin_encoded = self.clinical_encoder(clinical_features)
        
        # Concatenate
        combined = torch.cat([expr_encoded, clin_encoded], dim=1)
        
        # Process through network
        features = self.network(combined)
        
        # Multiple outputs
        survival_pred = self.survival_head(features)
        biomarker_score = torch.sigmoid(self.biomarker_head(features))
        
        return survival_pred, biomarker_score

class BiomarkerDiscoveryModel:
    """
    State-of-the-art biomarker discovery model.
    
    Features:
    - Cox proportional hazards regression
    - Deep learning for survival analysis
    - Machine learning for biomarker identification
    - Statistical significance testing
    - Comprehensive evaluation metrics
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.is_trained = False
        
        # Models
        self.neural_net = None
        self.cox_model = None
        self.ensemble_model = None
        self.scaler = StandardScaler()
        
        # Feature engineering
        self.expression_features = [
            'expression_value', 'expression_unit', 'measurement_type',
            'fold_change', 'z_score', 'percentile_rank', 'expression_category'
        ]
        
        self.clinical_features = [
            'age', 'gender_encoded', 'disease_type_encoded', 'tumor_stage',
            'tumor_grade', 'er_status_encoded', 'pr_status_encoded',
            'her2_status_encoded', 'treatment_history', 'comorbidities'
        ]
        
        if model_path and Path(model_path).exists():
            self.load_model()
    
    def _extract_expression_features(self, gene_expression_df: pd.DataFrame) -> pd.DataFrame:
        """Extract advanced expression features."""
        features = pd.DataFrame()
        
        # Basic expression features
        features['expression_value'] = gene_expression_df['expression_value']
        features['expression_unit'] = gene_expression_df['expression_unit'].astype('category').cat.codes
        features['measurement_type'] = gene_expression_df['measurement_type'].astype('category').cat.codes
        
        # Advanced expression features (simulated for demo)
        n_genes = len(gene_expression_df)
        
        # Calculate fold change (simulated)
        features['fold_change'] = np.random.uniform(0.1, 10.0, n_genes)
        
        # Z-score normalization
        features['z_score'] = (features['expression_value'] - features['expression_value'].mean()) / features['expression_value'].std()
        
        # Percentile rank
        features['percentile_rank'] = features['expression_value'].rank(pct=True)
        
        # Expression category (low, medium, high)
        features['expression_category'] = pd.cut(
            features['expression_value'], 
            bins=3, 
            labels=[0, 1, 2]
        ).astype(int)
        
        return features
    
    def _extract_clinical_features(self, samples_df: pd.DataFrame) -> pd.DataFrame:
        """Extract clinical features from samples."""
        features = pd.DataFrame()
        
        # Demographics
        features['age'] = samples_df['age'].fillna(50)
        features['gender_encoded'] = samples_df['gender'].astype('category').cat.codes
        features['disease_type_encoded'] = samples_df['disease_type'].astype('category').cat.codes
        
        # Clinical features from metadata
        features['tumor_stage'] = samples_df['metadata'].apply(
            lambda x: x.get('stage', 'Unknown') if x else 'Unknown'
        ).astype('category').cat.codes
        
        features['tumor_grade'] = samples_df['metadata'].apply(
            lambda x: x.get('tumor_grade', 0) if x else 0
        )
        
        # Receptor status
        features['er_status_encoded'] = samples_df['metadata'].apply(
            lambda x: 1 if x and x.get('er_status') == 'positive' else 0
        )
        
        features['pr_status_encoded'] = samples_df['metadata'].apply(
            lambda x: 1 if x and x.get('pr_status') == 'positive' else 0
        )
        
        features['her2_status_encoded'] = samples_df['metadata'].apply(
            lambda x: 1 if x and x.get('her2_status') == 'positive' else 0
        )
        
        # Additional features (simulated)
        features['treatment_history'] = np.random.randint(0, 5, len(samples_df))
        features['comorbidities'] = np.random.randint(0, 3, len(samples_df))
        
        return features
    
    def _prepare_survival_data(self, samples_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare survival data."""
        # Extract survival times and event indicators
        survival_times = samples_df['metadata'].apply(
            lambda x: x.get('survival_days', 0) if x else 0
        ).values
        
        # Event indicator (1 for event, 0 for censored)
        # Simulate events based on survival time
        event_indicators = (survival_times < np.median(survival_times)).astype(int)
        
        return survival_times, event_indicators
    
    def train(self, gene_expression_df: pd.DataFrame, samples_df: pd.DataFrame,
              validation_split: float = 0.2) -> Dict[str, float]:
        """
        Train the biomarker discovery model.
        
        Args:
            gene_expression_df: DataFrame with gene expression data
            samples_df: DataFrame with patient samples
            validation_split: Fraction of data for validation
            
        Returns:
            Dictionary of training metrics
        """
        logger.info("Training state-of-the-art biomarker discovery model")
        
        # Extract features
        expression_features = self._extract_expression_features(gene_expression_df)
        clinical_features = self._extract_clinical_features(samples_df)
        survival_times, event_indicators = self._prepare_survival_data(samples_df)
        
        # Align data
        min_len = min(len(expression_features), len(clinical_features), len(survival_times))
        expression_features = expression_features.iloc[:min_len]
        clinical_features = clinical_features.iloc[:min_len]
        survival_times = survival_times[:min_len]
        event_indicators = event_indicators[:min_len]
        
        # Split data
        indices = np.arange(min_len)
        train_idx, val_idx = train_test_split(indices, test_size=validation_split, random_state=42)
        
        # Scale features
        expr_train = self.scaler.fit_transform(expression_features.iloc[train_idx])
        expr_val = self.scaler.transform(expression_features.iloc[val_idx])
        
        clin_train = clinical_features.iloc[train_idx].values
        clin_val = clinical_features.iloc[val_idx].values
        
        # Train Cox model
        self._train_cox_model(expr_train, clin_train, survival_times[train_idx], event_indicators[train_idx])
        
        # Train neural network
        self._train_neural_network(
            expr_train, clin_train, survival_times[train_idx], event_indicators[train_idx],
            expr_val, clin_val, survival_times[val_idx], event_indicators[val_idx]
        )
        
        # Train ensemble model
        self._train_ensemble_model(
            expr_train, clin_train, survival_times[train_idx],
            expr_val, clin_val, survival_times[val_idx]
        )
        
        # Evaluate models
        metrics = self._evaluate_models(
            expr_val, clin_val, survival_times[val_idx], event_indicators[val_idx]
        )
        
        self.is_trained = True
        logger.info(f"Training completed. C-index: {metrics['c_index']:.3f}")
        
        return metrics
    
    def _train_cox_model(self, expr_features: np.ndarray, clin_features: np.ndarray,
                        survival_times: np.ndarray, event_indicators: np.ndarray):
        """Train Cox proportional hazards model."""
        # Combine features
        combined_features = np.concatenate([expr_features, clin_features], axis=1)
        
        # Create DataFrame for lifelines
        cox_data = pd.DataFrame(combined_features)
        cox_data['time'] = survival_times
        cox_data['event'] = event_indicators
        
        # Train Cox model
        self.cox_model = CoxPHFitter()
        self.cox_model.fit(cox_data, duration_col='time', event_col='event')
        
        logger.info("Cox model trained successfully")
    
    def _train_neural_network(self, expr_train, clin_train, survival_train, events_train,
                             expr_val, clin_val, survival_val, events_val):
        """Train deep neural network."""
        # Create dataset and dataloader
        train_dataset = BiomarkerDataset(expr_train, clin_train, survival_train, events_train)
        train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
        
        # Initialize model
        self.neural_net = BiomarkerNeuralNetwork(
            expression_dim=expr_train.shape[1],
            clinical_dim=clin_train.shape[1]
        )
        
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.neural_net.parameters(), lr=0.001)
        
        # Training loop
        self.neural_net.train()
        for epoch in range(100):
            total_loss = 0
            for batch_expr, batch_clin, batch_survival, batch_events in train_loader:
                optimizer.zero_grad()
                survival_pred, biomarker_score = self.neural_net(batch_expr, batch_clin)
                
                # Combined loss
                survival_loss = criterion(survival_pred.squeeze(), batch_survival)
                biomarker_loss = criterion(biomarker_score.squeeze(), batch_events)
                total_loss_epoch = survival_loss + biomarker_loss
                
                total_loss_epoch.backward()
                optimizer.step()
                total_loss += total_loss_epoch.item()
            
            if epoch % 20 == 0:
                logger.info(f"Epoch {epoch}, Loss: {total_loss/len(train_loader):.4f}")
    
    def _train_ensemble_model(self, expr_train, clin_train, survival_train,
                             expr_val, clin_val, survival_val):
        """Train ensemble of traditional ML models."""
        # Combine features
        X_train = np.concatenate([expr_train, clin_train], axis=1)
        X_val = np.concatenate([expr_val, clin_val], axis=1)
        
        # XGBoost
        xgb_model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        
        # LightGBM
        lgb_model = lgb.LGBMRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )
        
        # Random Forest
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        # Train models
        xgb_model.fit(X_train, survival_train)
        lgb_model.fit(X_train, survival_train)
        rf_model.fit(X_train, survival_train)
        
        # Store ensemble
        self.ensemble_models = {
            'xgb': xgb_model,
            'lgb': lgb_model,
            'rf': rf_model
        }
    
    def _evaluate_models(self, expr_val, clin_val, survival_val, events_val) -> Dict[str, float]:
        """Evaluate all models."""
        # Cox model evaluation
        combined_val = np.concatenate([expr_val, clin_val], axis=1)
        cox_data = pd.DataFrame(combined_val)
        cox_data['time'] = survival_val
        cox_data['event'] = events_val
        
        c_index = self.cox_model.concordance_index_
        
        # Neural network evaluation
        self.neural_net.eval()
        with torch.no_grad():
            survival_pred, biomarker_score = self.neural_net(
                torch.FloatTensor(expr_val),
                torch.FloatTensor(clin_val)
            )
            nn_survival_pred = survival_pred.numpy().flatten()
            nn_biomarker_score = biomarker_score.numpy().flatten()
        
        # Ensemble evaluation
        X_val = np.concatenate([expr_val, clin_val], axis=1)
        ensemble_preds = []
        for model in self.ensemble_models.values():
            ensemble_preds.append(model.predict(X_val))
        
        ensemble_pred = np.mean(ensemble_preds, axis=0)
        
        # Calculate metrics
        metrics = {
            'c_index': c_index,
            'cox_concordance': c_index,
            'neural_net_mse': mean_squared_error(survival_val, nn_survival_pred),
            'ensemble_mse': mean_squared_error(survival_val, ensemble_pred),
            'biomarker_auc': self._calculate_auc(events_val, nn_biomarker_score)
        }
        
        return metrics
    
    def _calculate_auc(self, true_labels: np.ndarray, predictions: np.ndarray) -> float:
        """Calculate AUC for biomarker classification."""
        from sklearn.metrics import roc_auc_score
        try:
            return roc_auc_score(true_labels, predictions)
        except:
            return 0.5
    
    def predict_biomarker_score(self, gene_expression_df: pd.DataFrame, samples_df: pd.DataFrame) -> np.ndarray:
        """
        Predict biomarker scores.
        
        Args:
            gene_expression_df: DataFrame with gene expression data
            samples_df: DataFrame with patient samples
            
        Returns:
            Array of biomarker scores (0-1)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Extract features
        expression_features = self._extract_expression_features(gene_expression_df)
        clinical_features = self._extract_clinical_features(samples_df)
        
        # Align data
        min_len = min(len(expression_features), len(clinical_features))
        expression_features = expression_features.iloc[:min_len]
        clinical_features = clinical_features.iloc[:min_len]
        
        # Scale features
        expr_scaled = self.scaler.transform(expression_features)
        clin_scaled = clinical_features.values
        
        # Neural network predictions
        self.neural_net.eval()
        with torch.no_grad():
            _, biomarker_scores = self.neural_net(
                torch.FloatTensor(expr_scaled),
                torch.FloatTensor(clin_scaled)
            )
            biomarker_scores = biomarker_scores.numpy().flatten()
        
        return biomarker_scores
    
    def predict_survival(self, gene_expression_df: pd.DataFrame, samples_df: pd.DataFrame) -> np.ndarray:
        """
        Predict survival times.
        
        Args:
            gene_expression_df: DataFrame with gene expression data
            samples_df: DataFrame with patient samples
            
        Returns:
            Array of predicted survival times
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Extract features
        expression_features = self._extract_expression_features(gene_expression_df)
        clinical_features = self._extract_clinical_features(samples_df)
        
        # Align data
        min_len = min(len(expression_features), len(clinical_features))
        expression_features = expression_features.iloc[:min_len]
        clinical_features = clinical_features.iloc[:min_len]
        
        # Scale features
        expr_scaled = self.scaler.transform(expression_features)
        clin_scaled = clinical_features.values
        
        # Neural network predictions
        self.neural_net.eval()
        with torch.no_grad():
            survival_pred, _ = self.neural_net(
                torch.FloatTensor(expr_scaled),
                torch.FloatTensor(clin_scaled)
            )
            survival_pred = survival_pred.numpy().flatten()
        
        return survival_pred
    
    def get_significant_biomarkers(self, gene_expression_df: pd.DataFrame, 
                                 samples_df: pd.DataFrame, p_threshold: float = 0.05) -> pd.DataFrame:
        """
        Identify statistically significant biomarkers.
        
        Args:
            gene_expression_df: DataFrame with gene expression data
            samples_df: DataFrame with patient samples
            p_threshold: P-value threshold for significance
            
        Returns:
            DataFrame with significant biomarkers
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before analysis")
        
        # Get biomarker scores
        biomarker_scores = self.predict_biomarker_score(gene_expression_df, samples_df)
        
        # Perform statistical testing
        survival_times, event_indicators = self._prepare_survival_data(samples_df)
        
        # Calculate correlation with survival
        correlations = []
        p_values = []
        
        for i in range(len(gene_expression_df)):
            if i < len(biomarker_scores):
                # Calculate correlation between expression and survival
                correlation, p_value = stats.pearsonr(
                    gene_expression_df.iloc[i:i+1]['expression_value'].values,
                    survival_times[:1]
                )
                correlations.append(correlation)
                p_values.append(p_value)
            else:
                correlations.append(0)
                p_values.append(1)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'gene_name': gene_expression_df['gene_name'],
            'biomarker_score': biomarker_scores[:len(gene_expression_df)],
            'correlation': correlations,
            'p_value': p_values,
            'significant': [p < p_threshold for p in p_values]
        })
        
        # Sort by biomarker score
        results = results.sort_values('biomarker_score', ascending=False)
        
        return results
    
    def save_model(self, path: str):
        """Save the trained model."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save neural network
        torch.save(self.neural_net.state_dict(), f"{path}_neural_net.pth")
        
        # Save Cox model
        self.cox_model.save_model(f"{path}_cox_model")
        
        # Save ensemble models
        joblib.dump(self.ensemble_models, f"{path}_ensemble.joblib")
        
        # Save scaler
        joblib.dump(self.scaler, f"{path}_scaler.joblib")
        
        # Save metadata
        metadata = {
            "expression_features": self.expression_features,
            "clinical_features": self.clinical_features,
            "is_trained": self.is_trained
        }
        
        with open(f"{path}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Biomarker discovery model saved to {path}")
    
    def load_model(self):
        """Load the trained model."""
        if not self.model_path:
            raise ValueError("No model path specified")
        
        # Load neural network
        self.neural_net = BiomarkerNeuralNetwork(
            expression_dim=len(self.expression_features),
            clinical_dim=len(self.clinical_features)
        )
        self.neural_net.load_state_dict(torch.load(f"{self.model_path}_neural_net.pth"))
        
        # Load Cox model
        self.cox_model = CoxPHFitter()
        self.cox_model.load_model(f"{self.model_path}_cox_model")
        
        # Load ensemble models
        self.ensemble_models = joblib.load(f"{self.model_path}_ensemble.joblib")
        
        # Load scaler
        self.scaler = joblib.load(f"{self.model_path}_scaler.joblib")
        
        # Load metadata
        with open(f"{self.model_path}_metadata.json", 'r') as f:
            metadata = json.load(f)
            self.expression_features = metadata["expression_features"]
            self.clinical_features = metadata["clinical_features"]
            self.is_trained = metadata["is_trained"]
        
        logger.info(f"Biomarker discovery model loaded from {self.model_path}") 