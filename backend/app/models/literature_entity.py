#!/usr/bin/env python3
"""
Literature Entity Model

SQLAlchemy model for literature_entities table in the genomics platform.
"""

from sqlalchemy import Column, String, Float, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class LiteratureEntity(Base):
    """Literature entity model representing extracted biomedical entities."""
    
    __tablename__ = "literature_entities"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Publication information
    pmid = Column(String(20), nullable=False, index=True)
    title = Column(String(500))
    abstract = Column(String(5000))
    
    # Entity information
    entity_type = Column(String(100), nullable=False, index=True)  # gene, disease, drug, etc.
    entity_id = Column(String(255), index=True)
    entity_name = Column(String(255), nullable=False, index=True)
    
    # Confidence and source
    confidence_score = Column(Float, index=True)
    source = Column(String(100), index=True)  # PubMed, ChEMBL, etc.
    
    # Additional metadata
    meta_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<LiteratureEntity(entity='{self.entity_name}', type='{self.entity_type}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "pmid": self.pmid,
            "title": self.title,
            "abstract": self.abstract,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "confidence_score": self.confidence_score,
            "source": self.source,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 