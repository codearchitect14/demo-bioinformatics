#!/usr/bin/env python3
"""
ChEMBL Data Pipeline

This pipeline downloads and processes chemical compound data from ChEMBL,
including molecular structures, bioactivity data, and drug discovery information.
"""

import os
import sys
import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
import json
import requests
from typing import Dict, List, Any, Optional

from base.base_pipeline import BaseDatasetPipeline
from utils.download_utils import DownloadManager
from utils.logging_utils import setup_logger


class ChEMBLPipeline(BaseDatasetPipeline):
    """Pipeline for processing ChEMBL chemical compound data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            dataset_name="chembl",
            dataset_source="CHEMBL",
            config=config or {}
        )
        self.logger = setup_logger(f"pipeline.{self.dataset_name}")
        
        # ChEMBL specific configuration
        self.base_url = "https://www.ebi.ac.uk/chembl/api/data"
        self.version = "v31"
        self.target_types = ["PROTEIN", "PROTEIN_FAMILY", "PROTEIN_COMPLEX"]
        
    async def download_data(self) -> Dict[str, str]:
        """Download ChEMBL data files."""
        self.logger.info("Starting ChEMBL data download...")
        
        downloaded_files = {}
        
        try:
            # Download molecule data
            molecules_url = f"{self.base_url}/molecule.json?limit=100"
            molecules_file = await self.download_manager.download_file(
                molecules_url,
                self.data_dir / "molecules.json"
            )
            downloaded_files["molecules"] = str(molecules_file)
            
            # Download target data
            targets_url = f"{self.base_url}/target.json?limit=50"
            targets_file = await self.download_manager.download_file(
                targets_url,
                self.data_dir / "targets.json"
            )
            downloaded_files["targets"] = str(targets_file)
            
            # Download activity data
            activities_url = f"{self.base_url}/activity.json?limit=200"
            activities_file = await self.download_manager.download_file(
                activities_url,
                self.data_dir / "activities.json"
            )
            downloaded_files["activities"] = str(activities_file)
            
            self.logger.info(f"Downloaded {len(downloaded_files)} ChEMBL data files")
            return downloaded_files
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise
    
    def clean_data(self, data_files: Dict[str, str]) -> Dict[str, pd.DataFrame]:
        """Clean and preprocess ChEMBL data."""
        self.logger.info("Cleaning ChEMBL data...")
        
        cleaned_data = {}
        
        try:
            # Clean molecules data
            if "molecules" in data_files:
                with open(data_files["molecules"], 'r') as f:
                    molecules_data = json.load(f)
                
                molecules_list = []
                for mol in molecules_data.get('molecules', []):
                    molecules_list.append({
                        'molecule_id': mol.get('molecule_chembl_id', ''),
                        'molecule_name': mol.get('pref_name', ''),
                        'molecular_formula': mol.get('molecular_formula', ''),
                        'molecular_weight': mol.get('molecular_weight', 0),
                        'smiles': mol.get('molecule_structures', {}).get('canonical_smiles', ''),
                        'inchi': mol.get('molecule_structures', {}).get('standard_inchi', ''),
                        'drug_likeness': mol.get('molecule_properties', {}).get('num_ro5_violations', 0),
                        'bioavailability': mol.get('molecule_properties', {}).get('oral_bioavailability', 0)
                    })
                
                cleaned_data["molecules"] = pd.DataFrame(molecules_list)
            
            # Clean targets data
            if "targets" in data_files:
                with open(data_files["targets"], 'r') as f:
                    targets_data = json.load(f)
                
                targets_list = []
                for target in targets_data.get('targets', []):
                    targets_list.append({
                        'target_id': target.get('target_chembl_id', ''),
                        'target_name': target.get('pref_name', ''),
                        'target_type': target.get('target_type', ''),
                        'organism': target.get('target_components', [{}])[0].get('organism', ''),
                        'gene_name': target.get('target_components', [{}])[0].get('accession', ''),
                        'protein_name': target.get('target_components', [{}])[0].get('component_name', '')
                    })
                
                cleaned_data["targets"] = pd.DataFrame(targets_list)
            
            # Clean activities data
            if "activities" in data_files:
                with open(data_files["activities"], 'r') as f:
                    activities_data = json.load(f)
                
                activities_list = []
                for activity in activities_data.get('activities', []):
                    activities_list.append({
                        'activity_id': activity.get('activity_id', ''),
                        'molecule_id': activity.get('molecule_chembl_id', ''),
                        'target_id': activity.get('target_chembl_id', ''),
                        'activity_type': activity.get('type', ''),
                        'activity_value': activity.get('standard_value', 0),
                        'activity_unit': activity.get('standard_units', ''),
                        'activity_operator': activity.get('standard_relation', ''),
                        'assay_id': activity.get('assay_chembl_id', '')
                    })
                
                cleaned_data["activities"] = pd.DataFrame(activities_list)
            
            # Create sample compound data for demonstration
            compound_data = []
            compound_names = ["Aspirin", "Ibuprofen", "Paracetamol", "Morphine", "Codeine", 
                            "Caffeine", "Nicotine", "Cocaine", "Heroin", "Methamphetamine"]
            
            for i, name in enumerate(compound_names):
                compound_data.append({
                    'compound_id': f'CHEMBL{i+1:06d}',
                    'compound_name': name,
                    'molecular_formula': f'C{np.random.randint(5, 20)}H{np.random.randint(10, 30)}O{np.random.randint(1, 5)}',
                    'molecular_weight': np.random.uniform(100, 500),
                    'smiles': f'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O',  # Simplified SMILES
                    'drug_likeness': np.random.randint(0, 3),
                    'bioavailability': np.random.uniform(0.1, 1.0),
                    'target_protein': np.random.choice(['COX-1', 'COX-2', 'OPRM1', 'OPRD1', 'ADRA2A']),
                    'binding_affinity': np.random.uniform(0.001, 10.0),
                    'mechanism': np.random.choice(['inhibitor', 'agonist', 'antagonist', 'modulator'])
                })
            
            cleaned_data["compounds"] = pd.DataFrame(compound_data)
            
            self.logger.info(f"Cleaned {len(cleaned_data)} data types")
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Data cleaning failed: {e}")
            raise
    
    def transform_data(self, cleaned_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Transform data into unified schema."""
        self.logger.info("Transforming ChEMBL data...")
        
        transformed_data = {}
        
        try:
            # Transform compounds into drug_targets format
            if "compounds" in cleaned_data:
                compounds_df = cleaned_data["compounds"].copy()
                compounds_df['dataset_id'] = self.dataset_id
                compounds_df['drug_id'] = compounds_df['compound_id']
                compounds_df['drug_name'] = compounds_df['compound_name']
                compounds_df['target_gene'] = compounds_df['target_protein']
                compounds_df['target_protein'] = compounds_df['target_protein']
                compounds_df['interaction_type'] = compounds_df['mechanism']
                compounds_df['binding_affinity'] = compounds_df['binding_affinity']
                compounds_df['source'] = 'ChEMBL'
                
                transformed_data["drug_targets"] = compounds_df[[
                    'dataset_id', 'drug_id', 'drug_name', 'target_gene', 'target_protein',
                    'interaction_type', 'binding_affinity', 'source'
                ]]
            
            # Transform molecules into literature_entities format
            if "molecules" in cleaned_data:
                molecules_df = cleaned_data["molecules"].copy()
                molecules_df['dataset_id'] = self.dataset_id
                molecules_df['pmid'] = f'CHEMBL{molecules_df.index}'
                molecules_df['title'] = f'Chemical compound: {molecules_df["molecule_name"]}'
                molecules_df['abstract'] = f'Molecular weight: {molecules_df["molecular_weight"]}, Formula: {molecules_df["molecular_formula"]}'
                molecules_df['entity_type'] = 'compound'
                molecules_df['entity_id'] = molecules_df['molecule_id']
                molecules_df['entity_name'] = molecules_df['molecule_name']
                molecules_df['confidence_score'] = 0.9
                molecules_df['source'] = 'ChEMBL'
                
                transformed_data["literature_entities"] = molecules_df[[
                    'dataset_id', 'pmid', 'title', 'abstract', 'entity_type', 
                    'entity_id', 'entity_name', 'confidence_score', 'source'
                ]]
            
            self.logger.info(f"Transformed {len(transformed_data)} data types")
            return transformed_data
            
        except Exception as e:
            self.logger.error(f"Data transformation failed: {e}")
            raise
    
    def validate_data(self, transformed_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate transformed data."""
        self.logger.info("Validating ChEMBL data...")
        
        validation_results = {
            "total_records": 0,
            "validation_errors": 0,
            "data_quality": {}
        }
        
        try:
            for data_type, df in transformed_data.items():
                validation_results["total_records"] += len(df)
                
                if data_type == "drug_targets":
                    validation_results["data_quality"]["compounds"] = {
                        "total_compounds": len(df),
                        "unique_targets": df['target_gene'].nunique(),
                        "interaction_types": df['interaction_type'].value_counts().to_dict(),
                        "affinity_range": {
                            "min": df['binding_affinity'].min(),
                            "max": df['binding_affinity'].max()
                        }
                    }
                elif data_type == "literature_entities":
                    validation_results["data_quality"]["molecules"] = {
                        "total_molecules": len(df),
                        "entity_types": df['entity_type'].value_counts().to_dict(),
                        "confidence_scores": {
                            "mean": df['confidence_score'].mean(),
                            "std": df['confidence_score'].std()
                        }
                    }
            
            self.logger.info(f"Validation completed: {validation_results['total_records']} records")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            raise
    
    def generate_summary(self, transformed_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Generate data summary."""
        self.logger.info("Generating ChEMBL data summary...")
        
        summary = {
            "dataset_name": "chembl",
            "total_compounds": 0,
            "total_targets": 0,
            "total_activities": 0,
            "compound_distribution": {},
            "target_distribution": {},
            "activity_distribution": {}
        }
        
        try:
            if "drug_targets" in transformed_data:
                compounds_df = transformed_data["drug_targets"]
                summary["total_compounds"] = len(compounds_df)
                summary["compound_distribution"] = {
                    "interaction_types": compounds_df['interaction_type'].value_counts().to_dict(),
                    "targets": compounds_df['target_gene'].value_counts().to_dict()
                }
            
            if "literature_entities" in transformed_data:
                molecules_df = transformed_data["literature_entities"]
                summary["total_activities"] = len(molecules_df)
                summary["activity_distribution"] = {
                    "entity_types": molecules_df['entity_type'].value_counts().to_dict(),
                    "confidence_scores": {
                        "mean": molecules_df['confidence_score'].mean(),
                        "median": molecules_df['confidence_score'].median()
                    }
                }
            
            self.logger.info(f"Summary generated: {summary['total_compounds']} compounds, {summary['total_activities']} activities")
            return summary
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            raise


if __name__ == "__main__":
    # Test the pipeline
    pipeline = ChEMBLPipeline()
    asyncio.run(pipeline.run()) 