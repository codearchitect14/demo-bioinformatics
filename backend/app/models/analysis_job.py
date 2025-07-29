#!/usr/bin/env python3
"""
Analysis Job Model

SQLAlchemy model for analysis_jobs table in the genomics platform.
"""

from sqlalchemy import Column, String, DateTime, JSON, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class AnalysisJob(Base):
    """Analysis job model representing computational analysis workflows."""
    
    __tablename__ = "analysis_jobs"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Job information
    job_name = Column(String(255), nullable=False, index=True)
    job_type = Column(String(100), nullable=False, index=True)  # variant_analysis, drug_response, etc.
    status = Column(String(50), nullable=False, index=True)  # pending, running, completed, failed
    
    # Input and output
    input_data = Column(JSON)
    output_data = Column(JSON)
    parameters = Column(JSON)
    
    # Execution details
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    
    # Additional metadata
    meta_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AnalysisJob(id='{self.id}', name='{self.job_name}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "job_name": self.job_name,
            "job_type": self.job_type,
            "status": self.status,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "parameters": self.parameters,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 