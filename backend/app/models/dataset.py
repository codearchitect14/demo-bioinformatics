#!/usr/bin/env python3
"""
Dataset Model

SQLAlchemy model for datasets table in the genomics platform.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Dataset(Base):
    """Dataset model representing genomics datasets."""
    
    __tablename__ = "datasets"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    
    # Statistics
    total_samples = Column(Integer, default=0)
    total_variants = Column(Integer, default=0)
    
    # Metadata
    meta_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    variants = relationship("Variant", back_populates="dataset", cascade="all, delete-orphan")
    samples = relationship("Sample", back_populates="dataset", cascade="all, delete-orphan")
    gene_expressions = relationship("GeneExpression", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset(id='{self.id}', name='{self.name}', source='{self.source}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "description": self.description,
            "total_samples": self.total_samples,
            "total_variants": self.total_variants,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 