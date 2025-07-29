"""
Data validation utilities for genomic datasets.

This module provides comprehensive data validation capabilities including
schema validation, business logic validation, and statistical validation.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime

from utils.logging_utils import setup_logger


class DataValidator:
    """
    Comprehensive data validator for genomic datasets.
    
    Provides methods for validating data quality, completeness, consistency,
    and accuracy across different genomic data types.
    """
    
    def __init__(self):
        """Initialize the data validator."""
        self.logger = setup_logger("data_validator")
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_schema(
        self, 
        data: pd.DataFrame, 
        schema: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate data against a predefined schema.
        
        Args:
            data: DataFrame to validate
            schema: Schema definition dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Check required columns
            required_columns = schema.get("required_columns", [])
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                errors.append(f"Missing required columns: {missing_columns}")
            
            # Check data types
            for column, expected_type in schema.get("column_types", {}).items():
                if column in data.columns:
                    if not self._validate_column_type(data[column], expected_type):
                        errors.append(f"Column {column} has incorrect data type. Expected: {expected_type}")
            
            # Check value ranges
            for column, range_config in schema.get("value_ranges", {}).items():
                if column in data.columns:
                    range_errors = self._validate_value_range(data[column], range_config)
                    errors.extend(range_errors)
            
            # Check unique constraints
            for column in schema.get("unique_columns", []):
                if column in data.columns and data[column].duplicated().any():
                    errors.append(f"Column {column} contains duplicate values")
            
            # Check foreign key constraints
            for fk_config in schema.get("foreign_keys", []):
                fk_errors = self._validate_foreign_key(data, fk_config)
                errors.extend(fk_errors)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            self.logger.error(f"Schema validation failed: {str(e)}")
            return False, [f"Schema validation error: {str(e)}"]
    
    def validate_completeness(
        self, 
        data: pd.DataFrame, 
        required_fields: List[str],
        threshold: float = 0.95
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Validate data completeness.
        
        Args:
            data: DataFrame to validate
            required_fields: List of required field names
            threshold: Minimum completeness threshold (0.0 to 1.0)
            
        Returns:
            Tuple of (is_complete, completeness_scores)
        """
        completeness_scores = {}
        
        for field in required_fields:
            if field in data.columns:
                completeness = 1 - (data[field].isna().sum() / len(data))
                completeness_scores[field] = completeness
            else:
                completeness_scores[field] = 0.0
        
        overall_completeness = np.mean(list(completeness_scores.values()))
        is_complete = overall_completeness >= threshold
        
        if not is_complete:
            self.logger.warning(f"Data completeness below threshold: {overall_completeness:.2f} < {threshold}")
        
        return is_complete, completeness_scores
    
    def validate_consistency(
        self, 
        data: pd.DataFrame, 
        consistency_rules: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """
        Validate data consistency using business rules.
        
        Args:
            data: DataFrame to validate
            consistency_rules: List of consistency rule dictionaries
            
        Returns:
            Tuple of (is_consistent, list_of_violations)
        """
        violations = []
        
        for rule in consistency_rules:
            rule_type = rule.get("type")
            
            if rule_type == "conditional":
                violations.extend(self._validate_conditional_rule(data, rule))
            elif rule_type == "cross_field":
                violations.extend(self._validate_cross_field_rule(data, rule))
            elif rule_type == "format":
                violations.extend(self._validate_format_rule(data, rule))
            elif rule_type == "reference":
                violations.extend(self._validate_reference_rule(data, rule))
        
        return len(violations) == 0, violations
    
    def validate_statistical_properties(
        self, 
        data: pd.DataFrame, 
        numeric_columns: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate statistical properties of numeric columns.
        
        Args:
            data: DataFrame to validate
            numeric_columns: List of numeric column names
            
        Returns:
            Dictionary of statistical properties for each column
        """
        stats = {}
        
        for column in numeric_columns:
            if column in data.columns and data[column].dtype in ['int64', 'float64']:
                col_data = data[column].dropna()
                
                if len(col_data) > 0:
                    stats[column] = {
                        "count": len(col_data),
                        "mean": float(col_data.mean()),
                        "std": float(col_data.std()),
                        "min": float(col_data.min()),
                        "max": float(col_data.max()),
                        "q25": float(col_data.quantile(0.25)),
                        "q50": float(col_data.quantile(0.50)),
                        "q75": float(col_data.quantile(0.75)),
                        "outliers": self._detect_outliers(col_data)
                    }
        
        return stats
    
    def validate_genomic_data(
        self, 
        data: pd.DataFrame, 
        data_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate genomic data specific to data type.
        
        Args:
            data: DataFrame containing genomic data
            data_type: Type of genomic data ('variants', 'expression', 'clinical')
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if data_type == "variants":
            errors.extend(self._validate_variant_data(data))
        elif data_type == "expression":
            errors.extend(self._validate_expression_data(data))
        elif data_type == "clinical":
            errors.extend(self._validate_clinical_data(data))
        else:
            errors.append(f"Unknown genomic data type: {data_type}")
        
        return len(errors) == 0, errors
    
    def _validate_column_type(self, series: pd.Series, expected_type: str) -> bool:
        """Validate column data type."""
        try:
            if expected_type == "string":
                return series.dtype == 'object'
            elif expected_type == "integer":
                return series.dtype in ['int64', 'int32']
            elif expected_type == "float":
                return series.dtype in ['float64', 'float32']
            elif expected_type == "datetime":
                return pd.api.types.is_datetime64_any_dtype(series)
            elif expected_type == "boolean":
                return series.dtype == 'bool'
            else:
                return True
        except Exception:
            return False
    
    def _validate_value_range(
        self, 
        series: pd.Series, 
        range_config: Dict[str, Any]
    ) -> List[str]:
        """Validate value ranges for a column."""
        errors = []
        
        min_val = range_config.get("min")
        max_val = range_config.get("max")
        allowed_values = range_config.get("allowed_values")
        
        if min_val is not None and series.min() < min_val:
            errors.append(f"Values below minimum {min_val}")
        
        if max_val is not None and series.max() > max_val:
            errors.append(f"Values above maximum {max_val}")
        
        if allowed_values is not None:
            invalid_values = series[~series.isin(allowed_values)]
            if len(invalid_values) > 0:
                errors.append(f"Invalid values found: {invalid_values.unique()}")
        
        return errors
    
    def _validate_foreign_key(
        self, 
        data: pd.DataFrame, 
        fk_config: Dict[str, Any]
    ) -> List[str]:
        """Validate foreign key constraints."""
        errors = []
        
        column = fk_config.get("column")
        reference_table = fk_config.get("reference_table")
        reference_column = fk_config.get("reference_column")
        
        if column in data.columns:
            # This would typically check against the reference table
            # For now, we'll just check for null values in foreign key columns
            if data[column].isna().any():
                errors.append(f"Foreign key column {column} contains null values")
        
        return errors
    
    def _validate_conditional_rule(
        self, 
        data: pd.DataFrame, 
        rule: Dict[str, Any]
    ) -> List[str]:
        """Validate conditional business rules."""
        violations = []
        
        condition = rule.get("condition")
        consequence = rule.get("consequence")
        
        if condition and consequence:
            # Apply condition to data
            mask = data.eval(condition)
            violating_rows = data[mask]
            
            if len(violating_rows) > 0:
                violations.append(f"Conditional rule violation: {condition} -> {consequence}")
        
        return violations
    
    def _validate_cross_field_rule(
        self, 
        data: pd.DataFrame, 
        rule: Dict[str, Any]
    ) -> List[str]:
        """Validate cross-field business rules."""
        violations = []
        
        field1 = rule.get("field1")
        field2 = rule.get("field2")
        relationship = rule.get("relationship")
        
        if field1 in data.columns and field2 in data.columns:
            if relationship == "equal":
                if not (data[field1] == data[field2]).all():
                    violations.append(f"Cross-field rule violation: {field1} != {field2}")
            elif relationship == "greater_than":
                if not (data[field1] > data[field2]).all():
                    violations.append(f"Cross-field rule violation: {field1} <= {field2}")
        
        return violations
    
    def _validate_format_rule(
        self, 
        data: pd.DataFrame, 
        rule: Dict[str, Any]
    ) -> List[str]:
        """Validate format rules."""
        violations = []
        
        column = rule.get("column")
        pattern = rule.get("pattern")
        
        if column in data.columns and pattern:
            import re
            invalid_rows = data[~data[column].astype(str).str.match(pattern, na=False)]
            if len(invalid_rows) > 0:
                violations.append(f"Format rule violation in {column}: {pattern}")
        
        return violations
    
    def _validate_reference_rule(
        self, 
        data: pd.DataFrame, 
        rule: Dict[str, Any]
    ) -> List[str]:
        """Validate reference data rules."""
        violations = []
        
        column = rule.get("column")
        reference_data = rule.get("reference_data")
        
        if column in data.columns and reference_data:
            invalid_values = data[~data[column].isin(reference_data)]
            if len(invalid_values) > 0:
                violations.append(f"Reference rule violation in {column}")
        
        return violations
    
    def _detect_outliers(self, series: pd.Series, method: str = "iqr") -> int:
        """Detect outliers in a numeric series."""
        if method == "iqr":
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            return len(outliers)
        else:
            return 0
    
    def _validate_variant_data(self, data: pd.DataFrame) -> List[str]:
        """Validate variant-specific data."""
        errors = []
        
        # Check chromosome format
        if "chromosome" in data.columns:
            valid_chromosomes = [str(i) for i in range(1, 23)] + ["X", "Y", "MT"]
            invalid_chromosomes = data[~data["chromosome"].isin(valid_chromosomes)]
            if len(invalid_chromosomes) > 0:
                errors.append("Invalid chromosome values found")
        
        # Check position values
        if "position" in data.columns:
            if (data["position"] <= 0).any():
                errors.append("Position values must be positive")
        
        # Check allele format
        if "reference_allele" in data.columns and "alternate_allele" in data.columns:
            # Basic allele format validation
            allele_pattern = r'^[ACGTN]+$'
            import re
            invalid_ref = data[~data["reference_allele"].astype(str).str.match(allele_pattern, na=False)]
            invalid_alt = data[~data["alternate_allele"].astype(str).str.match(allele_pattern, na=False)]
            if len(invalid_ref) > 0 or len(invalid_alt) > 0:
                errors.append("Invalid allele format found")
        
        return errors
    
    def _validate_expression_data(self, data: pd.DataFrame) -> List[str]:
        """Validate gene expression data."""
        errors = []
        
        # Check expression values
        expression_columns = [col for col in data.columns if "expression" in col.lower()]
        for col in expression_columns:
            if data[col].dtype in ['int64', 'float64']:
                if (data[col] < 0).any():
                    errors.append(f"Negative expression values found in {col}")
        
        return errors
    
    def _validate_clinical_data(self, data: pd.DataFrame) -> List[str]:
        """Validate clinical data."""
        errors = []
        
        # Check age values
        if "age" in data.columns:
            if (data["age"] < 0).any() or (data["age"] > 150).any():
                errors.append("Invalid age values found")
        
        # Check gender values
        if "gender" in data.columns:
            valid_genders = ["M", "F", "Male", "Female"]
            invalid_genders = data[~data["gender"].isin(valid_genders)]
            if len(invalid_genders) > 0:
                errors.append("Invalid gender values found")
        
        return errors
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        return {
            "total_errors": len(self.validation_errors),
            "total_warnings": len(self.validation_warnings),
            "errors": self.validation_errors,
            "warnings": self.validation_warnings
        }
    
    def clear_validation_results(self) -> None:
        """Clear validation results."""
        self.validation_errors = []
        self.validation_warnings = [] 