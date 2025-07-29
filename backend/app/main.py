#!/usr/bin/env python3
"""
Genomics Platform FastAPI Application

Main FastAPI application for the AI-powered genomics platform.
Provides REST API endpoints for variant analysis, drug discovery, and genomics data access.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any
import logging

# Import database and models
from app.database import engine, get_db, Base
from app.models import Dataset, Variant, Sample, GeneExpression, LiteratureEntity, DrugTarget
from app.api.v1 import datasets, variants, samples, drugs, health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Genomics Platform API...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Genomics Platform API...")


# Create FastAPI application
app = FastAPI(
    title="Genomics Platform API",
    description="AI-Powered Genomics Platform Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(datasets.router, prefix="/api/v1", tags=["Datasets"])
app.include_router(variants.router, prefix="/api/v1", tags=["Variants"])
app.include_router(samples.router, prefix="/api/v1", tags=["Samples"])
app.include_router(drugs.router, prefix="/api/v1", tags=["Drugs"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Genomics Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/v1")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Genomics Platform API",
        "version": "1.0.0",
        "description": "AI-Powered Genomics Platform Backend",
        "endpoints": {
            "health": "/api/v1/health",
            "datasets": "/api/v1/datasets",
            "variants": "/api/v1/variants",
            "samples": "/api/v1/samples",
            "drugs": "/api/v1/drugs"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 