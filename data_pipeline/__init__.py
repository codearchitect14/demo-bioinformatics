"""
AI-Powered Genomics Platform - Data Pipeline System

This package provides comprehensive data ingestion and processing pipelines
for genomic datasets including ClinVar, TCGA, and PubMed.

Author: GenomicsAI Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "GenomicsAI Team"

from .base.base_pipeline import BaseDatasetPipeline
from .datasets.clinvar_pipeline import ClinVarPipeline
from .datasets.tcga_pipeline import TCGAPipeline
from .datasets.pubmed_pipeline import PubMedPipeline
from .datasets.1000genomes_pipeline import ThousandGenomesPipeline
from .datasets.encode_pipeline import ENCODEPipeline
from .datasets.chembl_pipeline import ChEMBLPipeline

__all__ = [
    "BaseDatasetPipeline",
    "ClinVarPipeline", 
    "TCGAPipeline",
    "PubMedPipeline",
    "ThousandGenomesPipeline",
    "ENCODEPipeline",
    "ChEMBLPipeline"
] 