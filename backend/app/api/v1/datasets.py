#!/usr/bin/env python3
"""
Datasets API Endpoints

API endpoints for managing and querying genomics datasets.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
import logging
from app.database import get_db
from app.models import Dataset, Variant, Sample

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/datasets")
async def get_datasets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    source: Optional[str] = Query(None, description="Filter by data source"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all datasets with optional filtering and pagination.
    
    Args:
        skip: Number of records to skip
        limit: Number of records to return
        source: Filter by data source
        db: Database session
        
    Returns:
        Dict containing datasets and pagination info
    """
    try:
        # Build query
        query = db.query(Dataset)
        
        # Apply filters
        if source:
            query = query.filter(Dataset.source == source)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        datasets = query.offset(skip).limit(limit).all()
        
        return {
            "datasets": [dataset.to_dict() for dataset in datasets],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": skip + limit < total
            }
        }
    except Exception as e:
        logger.error(f"Failed to get datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get datasets: {str(e)}")


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get specific dataset by ID.
    
    Args:
        dataset_id: Dataset ID
        db: Database session
        
    Returns:
        Dict containing dataset information
    """
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        return dataset.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dataset: {str(e)}")


@router.get("/datasets/{dataset_id}/stats")
async def get_dataset_stats(dataset_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get statistics for a specific dataset.
    
    Args:
        dataset_id: Dataset ID
        db: Database session
        
    Returns:
        Dict containing dataset statistics
    """
    try:
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get variant statistics
        variant_stats = db.query(
            func.count(Variant.id).label("total_variants"),
            func.avg(Variant.quality_score).label("avg_quality_score"),
            func.avg(Variant.allele_frequency).label("avg_allele_frequency")
        ).filter(Variant.dataset_id == dataset_id).first()
        
        # Get sample statistics
        sample_stats = db.query(
            func.count(Sample.id).label("total_samples"),
            func.count(Sample.gender).label("samples_with_gender"),
            func.avg(Sample.age).label("avg_age")
        ).filter(Sample.dataset_id == dataset_id).first()
        
        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "source": dataset.source,
            "variants": {
                "total": variant_stats.total_variants or 0,
                "avg_quality_score": float(variant_stats.avg_quality_score) if variant_stats.avg_quality_score else None,
                "avg_allele_frequency": float(variant_stats.avg_allele_frequency) if variant_stats.avg_allele_frequency else None
            },
            "samples": {
                "total": sample_stats.total_samples or 0,
                "with_gender": sample_stats.samples_with_gender or 0,
                "avg_age": float(sample_stats.avg_age) if sample_stats.avg_age else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset stats for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dataset stats: {str(e)}")


@router.get("/datasets/sources")
async def get_data_sources(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get all available data sources.
    
    Args:
        db: Database session
        
    Returns:
        Dict containing data sources and their statistics
    """
    try:
        # Get unique sources with counts
        sources = db.query(
            Dataset.source,
            func.count(Dataset.id).label("dataset_count"),
            func.sum(Dataset.total_variants).label("total_variants"),
            func.sum(Dataset.total_samples).label("total_samples")
        ).group_by(Dataset.source).all()
        
        return {
            "sources": [
                {
                    "source": source.source,
                    "dataset_count": source.dataset_count,
                    "total_variants": source.total_variants or 0,
                    "total_samples": source.total_samples or 0
                }
                for source in sources
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get data sources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get data sources: {str(e)}") 