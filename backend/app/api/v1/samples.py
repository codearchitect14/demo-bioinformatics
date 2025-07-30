#!/usr/bin/env python3
"""
Samples API Endpoints

API endpoints for querying biological samples and gene expression data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
import logging
from app.database import get_db
from app.models import Sample, Dataset, GeneExpression

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
            "items": [sample.to_dict() for sample in samples],
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total
        }
    except Exception as e:
        logger.error(f"Failed to get samples: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get samples: {str(e)}")


@router.get("/gene-expression")
async def get_gene_expression(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    gene_name: Optional[str] = Query(None, description="Filter by gene name"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    sample_type: Optional[str] = Query(None, description="Filter by sample type"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get gene expression data with filtering and pagination.
    
    Args:
        skip: Number of records to skip
        limit: Number of records to return
        gene_name: Filter by gene name
        dataset_id: Filter by dataset ID
        sample_type: Filter by sample type
        db: Database session
        
    Returns:
        Dict containing gene expression data and pagination info
    """
    try:
        # Build query
        query = db.query(GeneExpression)
        
        # Apply filters
        if gene_name:
            query = query.filter(GeneExpression.gene_name.ilike(f"%{gene_name}%"))
        
        if dataset_id:
            query = query.filter(GeneExpression.dataset_id == dataset_id)
        
        if sample_type:
            # Join with samples table to filter by sample type
            query = query.join(Sample, GeneExpression.sample_id == Sample.id)
            query = query.filter(Sample.sample_type == sample_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        expressions = query.offset(skip).limit(limit).all()
        
        # Transform to frontend format with biomarker scores
        items = []
        for expr in expressions:
            expr_dict = expr.to_dict()
            
            # Calculate biomarker score based on expression value and significance
            expression_value = float(expr_dict['expression_value']) if expr_dict['expression_value'] else 0.0
            # Higher expression in tumor samples = higher biomarker potential
            biomarker_score = min(1.0, expression_value / 10.0)  # Normalize to 0-1
            
            # Calculate p-value (simulated based on expression level)
            p_value = max(0.001, 1.0 - (expression_value / 15.0))
            
            # Determine significance
            if p_value < 0.001:
                significance = "High"
            elif p_value < 0.01:
                significance = "Medium"
            else:
                significance = "Low"
            
            # Calculate fold change (simulated)
            fold_change = expression_value / 2.0 if expression_value > 0 else 1.0
            
            items.append({
                'id': expr_dict['id'],
                'gene_symbol': expr_dict['gene_name'],
                'expression_level': float(expr_dict['expression_value']) if expr_dict['expression_value'] else 0.0,
                'fold_change': round(fold_change, 2),
                'p_value': round(p_value, 4),
                'significance': significance,
                'biomarker_score': round(biomarker_score, 3),
                'sample_id': expr_dict['sample_id'],
                'dataset_id': expr_dict['dataset_id'],
                'expression_unit': expr_dict['expression_unit'],
                'measurement_type': expr_dict['measurement_type']
            })
        
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": skip + limit < total
        }
    except Exception as e:
        logger.error(f"Failed to get gene expression: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get gene expression: {str(e)}")


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
    except Exception as e:
        logger.error(f"Failed to get sample: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sample: {str(e)}") 