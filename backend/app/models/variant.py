#!/usr/bin/env python3
"""
Variant Model

SQLAlchemy model for variants table in the genomics platform.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Variant(Base):
    """Variant model representing genomic variants."""
    
    __tablename__ = "variants"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    
    # Genomic coordinates
    chromosome = Column(String(10), nullable=False, index=True)
    position = Column(Integer, nullable=False, index=True)
    
    # Allele information
    reference_allele = Column(String(50), nullable=False)
    alternate_allele = Column(String(50), nullable=False)
    
    # Variant classification
    variant_type = Column(String(50), index=True)  # SNP, INDEL, etc.
    clinical_significance = Column(String(100), index=True)  # pathogenic, benign, etc.
    
    # Quality metrics
    quality_score = Column(Float)
    allele_frequency = Column(Float, index=True)
    
    # Additional annotations
    annotations = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    dataset = relationship("Dataset", back_populates="variants")
    
    # Composite index for efficient genomic coordinate queries
    __table_args__ = (
        Index('idx_chromosome_position', 'chromosome', 'position'),
        Index('idx_dataset_chromosome', 'dataset_id', 'chromosome'),
    )
    
    def __repr__(self):
        return f"<Variant(id='{self.id}', chr{self.chromosome}:{self.position})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "chromosome": self.chromosome,
            "position": self.position,
            "reference_allele": self.reference_allele,
            "alternate_allele": self.alternate_allele,
            "variant_type": self.variant_type,
            "clinical_significance": self.clinical_significance,
            "quality_score": self.quality_score,
            "allele_frequency": self.allele_frequency,
            "annotations": self.annotations,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def genomic_coordinate(self):
        """Get genomic coordinate string."""
        return f"chr{self.chromosome}:{self.position}"
    
    @property
    def variant_id(self):
        """Get variant identifier string."""
        return f"{self.chromosome}_{self.position}_{self.reference_allele}_{self.alternate_allele}" 