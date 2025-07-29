"""
Data transformation utilities for genomic datasets.

This module provides utilities for transforming data from various sources
into a unified schema for the genomics platform.
"""

import logging
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import json

from utils.logging_utils import setup_logger


class DataTransformer:
    """
    Data transformer for converting genomic data to unified schema.
    
    Provides methods for transforming data from various sources into
    standardized formats for the genomics platform.
    """
    
    def __init__(self):
        """Initialize the data transformer."""
        self.logger = setup_logger("data_transformer")
        self.transformation_stats = {}
    
    def transform_to_unified_schema(
        self, 
        data: pd.DataFrame, 
        source_type: str,
        mapping_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Transform data to unified schema.
        
        Args:
            data: Input DataFrame
            source_type: Type of source data ('clinvar', 'tcga', 'pubmed')
            mapping_config: Column mapping configuration
            
        Returns:
            Transformed DataFrame with unified schema
        """
        try:
            self.logger.info(f"Transforming {source_type} data to unified schema")
            
            # Apply column mapping
            transformed_data = self._apply_column_mapping(data, mapping_config)
            
            # Apply data type conversions
            transformed_data = self._apply_data_type_conversions(transformed_data, mapping_config)
            
            # Apply value transformations
            transformed_data = self._apply_value_transformations(transformed_data, mapping_config)
            
            # Add metadata
            transformed_data = self._add_metadata(transformed_data, source_type)
            
            # Validate transformed data
            self._validate_transformed_data(transformed_data)
            
            self.logger.info(f"Successfully transformed {len(transformed_data)} records")
            return transformed_data
            
        except Exception as e:
            self.logger.error(f"Data transformation failed: {str(e)}")
            raise
    
    def _apply_column_mapping(
        self, 
        data: pd.DataFrame, 
        mapping_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply column mapping from source to target schema."""
        column_mapping = mapping_config.get("column_mapping", {})
        
        # Rename columns according to mapping
        renamed_data = data.rename(columns=column_mapping)
        
        # Add missing columns with default values
        required_columns = mapping_config.get("required_columns", [])
        for column in required_columns:
            if column not in renamed_data.columns:
                default_value = mapping_config.get("default_values", {}).get(column, None)
                renamed_data[column] = default_value
        
        return renamed_data
    
    def _apply_data_type_conversions(
        self, 
        data: pd.DataFrame, 
        mapping_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply data type conversions."""
        type_conversions = mapping_config.get("type_conversions", {})
        
        for column, target_type in type_conversions.items():
            if column in data.columns:
                try:
                    if target_type == "string":
                        data[column] = data[column].astype(str)
                    elif target_type == "integer":
                        data[column] = pd.to_numeric(data[column], errors='coerce').astype('Int64')
                    elif target_type == "float":
                        data[column] = pd.to_numeric(data[column], errors='coerce')
                    elif target_type == "datetime":
                        data[column] = pd.to_datetime(data[column], errors='coerce')
                    elif target_type == "boolean":
                        data[column] = data[column].astype(bool)
                except Exception as e:
                    self.logger.warning(f"Failed to convert column {column} to {target_type}: {str(e)}")
        
        return data
    
    def _apply_value_transformations(
        self, 
        data: pd.DataFrame, 
        mapping_config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Apply value transformations."""
        value_transformations = mapping_config.get("value_transformations", {})
        
        for column, transformation in value_transformations.items():
            if column in data.columns:
                try:
                    if transformation.get("type") == "normalize":
                        data[column] = self._normalize_values(data[column], transformation)
                    elif transformation.get("type") == "categorize":
                        data[column] = self._categorize_values(data[column], transformation)
                    elif transformation.get("type") == "encode":
                        data[column] = self._encode_values(data[column], transformation)
                    elif transformation.get("type") == "custom":
                        data[column] = self._apply_custom_transformation(data[column], transformation)
                except Exception as e:
                    self.logger.warning(f"Failed to transform column {column}: {str(e)}")
        
        return data
    
    def _normalize_values(self, series: pd.Series, config: Dict[str, Any]) -> pd.Series:
        """Normalize numeric values."""
        method = config.get("method", "min_max")
        
        if method == "min_max":
            min_val = series.min()
            max_val = series.max()
            if max_val > min_val:
                return (series - min_val) / (max_val - min_val)
            else:
                return series
        elif method == "z_score":
            mean_val = series.mean()
            std_val = series.std()
            if std_val > 0:
                return (series - mean_val) / std_val
            else:
                return series
        else:
            return series
    
    def _categorize_values(self, series: pd.Series, config: Dict[str, Any]) -> pd.Series:
        """Categorize values based on bins or categories."""
        bins = config.get("bins")
        labels = config.get("labels")
        
        if bins and labels:
            return pd.cut(series, bins=bins, labels=labels, include_lowest=True)
        else:
            return series
    
    def _encode_values(self, series: pd.Series, config: Dict[str, Any]) -> pd.Series:
        """Encode categorical values."""
        encoding_map = config.get("encoding_map", {})
        
        if encoding_map:
            return series.map(encoding_map)
        else:
            # Use pandas factorize for automatic encoding
            return pd.factorize(series)[0]
    
    def _apply_custom_transformation(self, series: pd.Series, config: Dict[str, Any]) -> pd.Series:
        """Apply custom transformation function."""
        # This would typically use a user-defined function
        # For now, return the original series
        return series
    
    def _add_metadata(self, data: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """Add metadata columns to the dataset."""
        data["source_type"] = source_type
        data["transformed_at"] = datetime.now().isoformat()
        data["data_version"] = "1.0"
        
        return data
    
    def _validate_transformed_data(self, data: pd.DataFrame) -> None:
        """Validate transformed data."""
        # Check for required columns
        required_columns = ["source_type", "transformed_at"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns after transformation: {missing_columns}")
        
        # Check for null values in critical columns
        critical_columns = ["id"] if "id" in data.columns else []
        for column in critical_columns:
            if data[column].isna().any():
                self.logger.warning(f"Critical column {column} contains null values")
    
    def transform_clinvar_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform ClinVar data to unified schema."""
        mapping_config = {
            "column_mapping": {
                "AlleleID": "variant_id",
                "Type": "variant_type",
                "Name": "variant_name",
                "GeneID": "gene_id",
                "GeneSymbol": "gene_symbol",
                "HGNC_ID": "hgnc_id",
                "ClinicalSignificance": "clinical_significance",
                "ClinSigSimple": "clinical_significance_simple",
                "LastEvaluated": "last_evaluated",
                "RS# (dbSNP)": "rs_id",
                "nsv/esv (dbVar)": "dbvar_id",
                "PhenotypeIDs": "phenotype_ids",
                "PhenotypeList": "phenotype_list",
                "Origin": "origin",
                "Assembly": "assembly",
                "ChromosomeAccession": "chromosome_accession",
                "Chromosome": "chromosome",
                "Start": "position",
                "Stop": "end_position",
                "ReferenceAllele": "reference_allele",
                "AlternateAllele": "alternate_allele",
                "Cytogenetic": "cytogenetic",
                "ReviewStatus": "review_status",
                "NumberSubmitters": "number_submitters",
                "Guidelines": "guidelines",
                "TestedInGTR": "tested_in_gtr",
                "OtherIDs": "other_ids",
                "SubmitterCategories": "submitter_categories",
                "VariationID": "variation_id"
            },
            "type_conversions": {
                "variant_id": "integer",
                "gene_id": "integer",
                "position": "integer",
                "end_position": "integer",
                "number_submitters": "integer",
                "last_evaluated": "datetime",
                "clinical_significance": "string",
                "variant_type": "string",
                "chromosome": "string"
            },
            "value_transformations": {
                "clinical_significance": {
                    "type": "categorize",
                    "categories": {
                        "Pathogenic": "pathogenic",
                        "Likely_pathogenic": "likely_pathogenic",
                        "Uncertain_significance": "uncertain_significance",
                        "Likely_benign": "likely_benign",
                        "Benign": "benign"
                    }
                }
            }
        }
        
        return self.transform_to_unified_schema(data, "clinvar", mapping_config)
    
    def transform_tcga_data(self, data: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Transform TCGA data to unified schema."""
        if data_type == "clinical":
            mapping_config = {
                "column_mapping": {
                    "Patient ID": "patient_id",
                    "Age": "age",
                    "Gender": "gender",
                    "Race": "race",
                    "Ethnicity": "ethnicity",
                    "Vital Status": "vital_status",
                    "Days to Death": "days_to_death",
                    "Days to Last Follow Up": "days_to_last_followup",
                    "Tumor Stage": "tumor_stage",
                    "Tumor Grade": "tumor_grade",
                    "Primary Diagnosis": "primary_diagnosis",
                    "Tumor Type": "tumor_type"
                },
                "type_conversions": {
                    "age": "integer",
                    "days_to_death": "integer",
                    "days_to_last_followup": "integer"
                }
            }
        elif data_type == "expression":
            mapping_config = {
                "column_mapping": {
                    "Gene": "gene_id",
                    "Gene Name": "gene_name",
                    "Sample": "sample_id"
                },
                "type_conversions": {
                    "expression_value": "float"
                }
            }
        else:
            mapping_config = {}
        
        return self.transform_to_unified_schema(data, f"tcga_{data_type}", mapping_config)
    
    def transform_pubmed_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform PubMed data to unified schema."""
        mapping_config = {
            "column_mapping": {
                "PMID": "pmid",
                "Title": "title",
                "Abstract": "abstract",
                "Authors": "authors",
                "Journal": "journal",
                "Publication Date": "publication_date",
                "MeSH Terms": "mesh_terms",
                "Keywords": "keywords"
            },
            "type_conversions": {
                "pmid": "integer",
                "publication_date": "datetime",
                "title": "string",
                "abstract": "string"
            },
            "value_transformations": {
                "mesh_terms": {
                    "type": "custom",
                    "function": "parse_mesh_terms"
                }
            }
        }
        
        return self.transform_to_unified_schema(data, "pubmed", mapping_config)
    
    def merge_datasets(
        self, 
        datasets: List[pd.DataFrame], 
        merge_strategy: str = "outer"
    ) -> pd.DataFrame:
        """
        Merge multiple datasets.
        
        Args:
            datasets: List of DataFrames to merge
            merge_strategy: Merge strategy ('inner', 'outer', 'left', 'right')
            
        Returns:
            Merged DataFrame
        """
        if not datasets:
            return pd.DataFrame()
        
        if len(datasets) == 1:
            return datasets[0]
        
        # Start with the first dataset
        merged_data = datasets[0]
        
        # Merge with remaining datasets
        for dataset in datasets[1:]:
            # Find common columns for merging
            common_columns = set(merged_data.columns) & set(dataset.columns)
            
            if common_columns:
                # Use the first common column as merge key
                merge_key = list(common_columns)[0]
                merged_data = merged_data.merge(
                    dataset, 
                    on=merge_key, 
                    how=merge_strategy,
                    suffixes=('', '_duplicate')
                )
            else:
                # If no common columns, concatenate
                merged_data = pd.concat([merged_data, dataset], axis=1)
        
        return merged_data
    
    def split_dataset(
        self, 
        data: pd.DataFrame, 
        split_config: Dict[str, Any]
    ) -> Dict[str, pd.DataFrame]:
        """
        Split dataset into training, validation, and test sets.
        
        Args:
            data: DataFrame to split
            split_config: Split configuration
            
        Returns:
            Dictionary containing split datasets
        """
        split_ratios = split_config.get("ratios", {"train": 0.7, "validation": 0.15, "test": 0.15})
        random_state = split_config.get("random_state", 42)
        stratify_column = split_config.get("stratify_column")
        
        # Validate split ratios
        total_ratio = sum(split_ratios.values())
        if abs(total_ratio - 1.0) > 0.01:
            raise ValueError(f"Split ratios must sum to 1.0, got {total_ratio}")
        
        # Shuffle data
        data_shuffled = data.sample(frac=1, random_state=random_state).reset_index(drop=True)
        
        # Calculate split indices
        n_samples = len(data_shuffled)
        train_end = int(n_samples * split_ratios["train"])
        val_end = train_end + int(n_samples * split_ratios["validation"])
        
        # Split data
        splits = {}
        splits["train"] = data_shuffled.iloc[:train_end]
        splits["validation"] = data_shuffled.iloc[train_end:val_end]
        splits["test"] = data_shuffled.iloc[val_end:]
        
        self.logger.info(f"Dataset split: train={len(splits['train'])}, "
                        f"validation={len(splits['validation'])}, test={len(splits['test'])}")
        
        return splits
    
    def get_transformation_stats(self) -> Dict[str, Any]:
        """Get transformation statistics."""
        return self.transformation_stats.copy()
    
    def clear_transformation_stats(self) -> None:
        """Clear transformation statistics."""
        self.transformation_stats = {} 