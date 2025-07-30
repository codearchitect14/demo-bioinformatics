#!/usr/bin/env python3
"""
Gene Expression Model

SQLAlchemy model for gene_expression table in the genomics platform.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class GeneExpression(Base):
    """Gene expression model representing transcriptomics data."""
    
    __tablename__ = "gene_expression"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    sample_id = Column(String, ForeignKey("samples.id"), nullable=False, index=True)
    
    # Gene information
    gene_name = Column(String(100), nullable=False, index=True)
    gene_id = Column(String(100), index=True)
    
    # Expression data
    expression_value = Column(Float, nullable=False)
    expression_unit = Column(String(50))  # TPM, FPKM, counts, etc.
    measurement_type = Column(String(100))  # RNA-seq, microarray, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    dataset = relationship("Dataset", back_populates="gene_expressions")
    sample = relationship("Sample", back_populates="gene_expressions")
    
    # Composite index for efficient gene expression queries
    __table_args__ = (
        Index('idx_gene_sample', 'gene_name', 'sample_id'),
        Index('idx_dataset_gene', 'dataset_id', 'gene_name'),
    )
    
    def __repr__(self):
        return f"<GeneExpression(gene='{self.gene_name}', sample='{self.sample_id}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "sample_id": self.sample_id,
            "gene_name": self.gene_name,
            "gene_id": self.gene_id,
            "expression_value": self.expression_value,
            "expression_unit": self.expression_unit,
            "measurement_type": self.measurement_type,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 