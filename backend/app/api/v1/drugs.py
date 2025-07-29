#!/usr/bin/env python3
"""
Drugs API Endpoints

API endpoints for querying drug-target interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
import logging
from app.database import get_db
from app.models import DrugTarget

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/drugs")
async def get_drugs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    drug_name: Optional[str] = Query(None, description="Filter by drug name"),
    target_gene: Optional[str] = Query(None, description="Filter by target gene"),
    interaction_type: Optional[str] = Query(None, description="Filter by interaction type"),
    source: Optional[str] = Query(None, description="Filter by data source"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get drug-target interactions with filtering and pagination.
    
    Args:
        skip: Number of records to skip
        limit: Number of records to return
        drug_name: Filter by drug name
        target_gene: Filter by target gene
        interaction_type: Filter by interaction type
        source: Filter by data source
        db: Database session
        
    Returns:
        Dict containing drug-target interactions and pagination info
    """
    try:
        # Build query
        query = db.query(DrugTarget)
        
        # Apply filters
        if drug_name:
            query = query.filter(DrugTarget.drug_name.ilike(f"%{drug_name}%"))
        
        if target_gene:
            query = query.filter(DrugTarget.target_gene.ilike(f"%{target_gene}%"))
        
        if interaction_type:
            query = query.filter(DrugTarget.interaction_type == interaction_type)
        
        if source:
            query = query.filter(DrugTarget.source == source)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        drugs = query.offset(skip).limit(limit).all()
        
        return {
            "drugs": [drug.to_dict() for drug in drugs],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": skip + limit < total
            }
        }
    except Exception as e:
        logger.error(f"Failed to get drugs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get drugs: {str(e)}")


@router.get("/drugs/{drug_id}")
async def get_drug(drug_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get specific drug by ID.
    
    Args:
        drug_id: Drug ID
        db: Database session
        
    Returns:
        Dict containing drug information
    """
    try:
        drug = db.query(DrugTarget).filter(DrugTarget.id == drug_id).first()
        
        if not drug:
            raise HTTPException(status_code=404, detail="Drug not found")
        
        return drug.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get drug {drug_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get drug: {str(e)}") 