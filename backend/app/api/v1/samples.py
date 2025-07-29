#!/usr/bin/env python3
"""
Samples API Endpoints

API endpoints for querying biological samples.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
import logging
from app.database import get_db
from app.models import Sample, Dataset

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/samples")
async def get_samples(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    sample_type: Optional[str] = Query(None, description="Filter by sample type"),
    disease_type: Optional[str] = Query(None, description="Filter by disease type"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get samples with filtering and pagination.
    
    Args:
        skip: Number of records to skip
        limit: Number of records to return
        dataset_id: Filter by dataset ID
        sample_type: Filter by sample type
        disease_type: Filter by disease type
        gender: Filter by gender
        db: Database session
        
    Returns:
        Dict containing samples and pagination info
    """
    try:
        # Build query
        query = db.query(Sample)
        
        # Apply filters
        if dataset_id:
            query = query.filter(Sample.dataset_id == dataset_id)
        
        if sample_type:
            query = query.filter(Sample.sample_type == sample_type)
        
        if disease_type:
            query = query.filter(Sample.disease_type == disease_type)
        
        if gender:
            query = query.filter(Sample.gender == gender)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        samples = query.offset(skip).limit(limit).all()
        
        return {
            "samples": [sample.to_dict() for sample in samples],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": skip + limit < total
            }
        }
    except Exception as e:
        logger.error(f"Failed to get samples: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get samples: {str(e)}")


@router.get("/samples/{sample_id}")
async def get_sample(sample_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get specific sample by ID.
    
    Args:
        sample_id: Sample ID
        db: Database session
        
    Returns:
        Dict containing sample information
    """
    try:
        sample = db.query(Sample).filter(Sample.id == sample_id).first()
        
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        
        return sample.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sample {sample_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sample: {str(e)}") 