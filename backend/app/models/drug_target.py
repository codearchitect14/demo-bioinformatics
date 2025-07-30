#!/usr/bin/env python3
"""
Drug Target Model

SQLAlchemy model for drug_targets table in the genomics platform.
"""

from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class DrugTarget(Base):
    """Drug target model representing drug-target interactions."""
    
    __tablename__ = "drug_targets"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Drug information
    drug_id = Column(String(255), nullable=False, index=True)
    drug_name = Column(String(255), nullable=False, index=True)
    
    # Target information
    target_gene = Column(String(100), index=True)
    target_protein = Column(String(255), index=True)
    
    # Interaction details
    interaction_type = Column(String(100), index=True)  # inhibitor, agonist, etc.
    binding_affinity = Column(Float, index=True)  # IC50, Ki, etc.
    
    # Source information
    source = Column(String(100), index=True)  # DrugBank, ChEMBL, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<DrugTarget(drug='{self.drug_name}', target='{self.target_protein}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "drug_id": self.drug_id,
            "drug_name": self.drug_name,
            "target_gene": self.target_gene,
            "target_protein": self.target_protein,
            "interaction_type": self.interaction_type,
            "binding_affinity": self.binding_affinity,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 