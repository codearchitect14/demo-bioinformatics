#!/usr/bin/env python3
"""
Variants API Endpoints

API endpoints for querying and analyzing genomic variants.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Any, Optional
import logging
from app.database import get_db
from app.models import Variant, Dataset

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/variants")
async def get_variants(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    chromosome: Optional[str] = Query(None, description="Filter by chromosome"),
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    variant_type: Optional[str] = Query(None, description="Filter by variant type"),
    clinical_significance: Optional[str] = Query(None, description="Filter by clinical significance"),
    min_quality_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum quality score"),
    max_allele_frequency: Optional[float] = Query(None, ge=0, le=1, description="Maximum allele frequency"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get variants with filtering and pagination.
    
    Args:
        skip: Number of records to skip
        limit: Number of records to return
        chromosome: Filter by chromosome
        dataset_id: Filter by dataset ID
        variant_type: Filter by variant type
        clinical_significance: Filter by clinical significance
        min_quality_score: Minimum quality score
        max_allele_frequency: Maximum allele frequency
        db: Database session
        
    Returns:
        Dict containing variants and pagination info
    """
    try:
        # Build query
        query = db.query(Variant)
        
        # Apply filters
        if chromosome:
            query = query.filter(Variant.chromosome == chromosome)
        
        if dataset_id:
            query = query.filter(Variant.dataset_id == dataset_id)
        
        if variant_type:
            query = query.filter(Variant.variant_type == variant_type)
        
        if clinical_significance:
            query = query.filter(Variant.clinical_significance == clinical_significance)
        
        if min_quality_score is not None:
            query = query.filter(Variant.quality_score >= min_quality_score)
        
        if max_allele_frequency is not None:
            query = query.filter(Variant.allele_frequency <= max_allele_frequency)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        variants = query.order_by(Variant.chromosome, Variant.position).offset(skip).limit(limit).all()
        
        return {
            "variants": [variant.to_dict() for variant in variants],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": skip + limit < total
            }
        }
    except Exception as e:
        logger.error(f"Failed to get variants: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get variants: {str(e)}")


@router.get("/variants/{variant_id}")
async def get_variant(variant_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get specific variant by ID.
    
    Args:
        variant_id: Variant ID
        db: Database session
        
    Returns:
        Dict containing variant information
    """
    try:
        variant = db.query(Variant).filter(Variant.id == variant_id).first()
        
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
        
        return variant.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get variant {variant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get variant: {str(e)}")


@router.get("/variants/search")
async def search_variants(
    chromosome: str = Query(..., description="Chromosome"),
    position: int = Query(..., ge=1, description="Position"),
    reference_allele: Optional[str] = Query(None, description="Reference allele"),
    alternate_allele: Optional[str] = Query(None, description="Alternate allele"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Search for variants by genomic coordinates.
    
    Args:
        chromosome: Chromosome
        position: Position
        reference_allele: Reference allele (optional)
        alternate_allele: Alternate allele (optional)
        db: Database session
        
    Returns:
        Dict containing matching variants
    """
    try:
        # Build query
        query = db.query(Variant).filter(
            and_(
                Variant.chromosome == chromosome,
                Variant.position == position
            )
        )
        
        # Add allele filters if provided
        if reference_allele:
            query = query.filter(Variant.reference_allele == reference_allele)
        
        if alternate_allele:
            query = query.filter(Variant.alternate_allele == alternate_allele)
        
        variants = query.all()
        
        return {
            "search_criteria": {
                "chromosome": chromosome,
                "position": position,
                "reference_allele": reference_allele,
                "alternate_allele": alternate_allele
            },
            "variants": [variant.to_dict() for variant in variants],
            "count": len(variants)
        }
    except Exception as e:
        logger.error(f"Failed to search variants: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search variants: {str(e)}")


@router.get("/variants/stats")
async def get_variant_stats(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get variant statistics.
    
    Args:
        dataset_id: Filter by dataset ID
        db: Database session
        
    Returns:
        Dict containing variant statistics
    """
    try:
        # Build query
        query = db.query(Variant)
        
        if dataset_id:
            query = query.filter(Variant.dataset_id == dataset_id)
        
        # Get statistics
        stats = db.query(
            func.count(Variant.id).label("total_variants"),
            func.avg(Variant.quality_score).label("avg_quality_score"),
            func.avg(Variant.allele_frequency).label("avg_allele_frequency"),
            func.count(func.distinct(Variant.chromosome)).label("chromosomes"),
            func.count(func.distinct(Variant.variant_type)).label("variant_types"),
            func.count(func.distinct(Variant.clinical_significance)).label("clinical_significances")
        ).select_from(query.subquery()).first()
        
        return {
            "total_variants": stats.total_variants or 0,
            "avg_quality_score": float(stats.avg_quality_score) if stats.avg_quality_score else None,
            "avg_allele_frequency": float(stats.avg_allele_frequency) if stats.avg_allele_frequency else None,
            "chromosomes": stats.chromosomes or 0,
            "variant_types": stats.variant_types or 0,
            "clinical_significances": stats.clinical_significances or 0
        }
    except Exception as e:
        logger.error(f"Failed to get variant stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get variant stats: {str(e)}") 