#!/usr/bin/env python3
"""
Sample Model

SQLAlchemy model for samples table in the genomics platform.
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Sample(Base):
    """Sample model representing biological samples."""
    
    __tablename__ = "samples"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    
    # Sample identification
    sample_id = Column(String(255), nullable=False, index=True)
    external_id = Column(String(255), index=True)
    
    # Sample characteristics
    sample_type = Column(String(100), index=True)  # tumor, normal, cell_line, etc.
    tissue_type = Column(String(100), index=True)
    disease_type = Column(String(100), index=True)
    
    # Demographics
    age = Column(Integer)
    gender = Column(String(10), index=True)
    
    # Additional metadata
    meta_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    dataset = relationship("Dataset", back_populates="samples")
    gene_expressions = relationship("GeneExpression", back_populates="sample", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Sample(id='{self.id}', sample_id='{self.sample_id}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "sample_id": self.sample_id,
            "external_id": self.external_id,
            "sample_type": self.sample_type,
            "tissue_type": self.tissue_type,
            "disease_type": self.disease_type,
            "age": self.age,
            "gender": self.gender,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 