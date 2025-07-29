#!/usr/bin/env python3
"""
Model Prediction Model

SQLAlchemy model for model_predictions table in the genomics platform.
"""

from sqlalchemy import Column, String, Float, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class ModelPrediction(Base):
    """Model prediction model representing ML model outputs."""
    
    __tablename__ = "model_predictions"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Model information
    model_name = Column(String(255), nullable=False, index=True)
    model_version = Column(String(50), index=True)
    prediction_type = Column(String(100), nullable=False, index=True)  # pathogenicity, drug_response, etc.
    
    # Input and output
    input_data = Column(JSON)
    prediction_value = Column(Float, nullable=False)
    confidence_score = Column(Float, index=True)
    
    # Additional metadata
    meta_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ModelPrediction(model='{self.model_name}', type='{self.prediction_type}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prediction_type": self.prediction_type,
            "input_data": self.input_data,
            "prediction_value": self.prediction_value,
            "confidence_score": self.confidence_score,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 