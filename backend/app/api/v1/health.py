#!/usr/bin/env python3
"""
Health Check API Endpoints

Health check and system status endpoints for the genomics platform.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from app.database import get_db, test_database_connection, get_database_info

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Dict containing health status
    """
    return {
        "status": "healthy",
        "service": "Genomics Platform API",
        "version": "1.0.0"
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check including database status.
    
    Args:
        db: Database session
        
    Returns:
        Dict containing detailed health status
    """
    try:
        # Test database connection
        db_healthy = test_database_connection()
        
        # Get database info
        db_info = get_database_info()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "Genomics Platform API",
            "version": "1.0.0",
            "database": {
                "status": "connected" if db_healthy else "disconnected",
                "info": db_info
            },
            "components": {
                "api": "healthy",
                "database": "healthy" if db_healthy else "unhealthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness check for Kubernetes/container orchestration.
    
    Args:
        db: Database session
        
    Returns:
        Dict containing readiness status
    """
    try:
        # Test database connection
        db_ready = test_database_connection()
        
        if not db_ready:
            raise HTTPException(status_code=503, detail="Database not ready")
        
        return {
            "status": "ready",
            "service": "Genomics Platform API",
            "database": "ready"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes/container orchestration.
    
    Returns:
        Dict containing liveness status
    """
    return {
        "status": "alive",
        "service": "Genomics Platform API"
    } 