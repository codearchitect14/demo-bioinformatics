"""
Logging utilities for data pipeline system.

This module provides comprehensive logging capabilities with structured logging,
log rotation, and different log levels for different components.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatters
    detailed_formatter = StructuredFormatter()
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger


class PipelineLogger:
    """Specialized logger for pipeline operations."""
    
    def __init__(self, pipeline_name: str, log_dir: str = "/logs"):
        """
        Initialize pipeline logger.
        
        Args:
            pipeline_name: Name of the pipeline
            log_dir: Directory for log files
        """
        self.pipeline_name = pipeline_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up different loggers for different purposes
        self.main_logger = setup_logger(
            f"pipeline.{pipeline_name}",
            log_file=str(self.log_dir / f"{pipeline_name}.log")
        )
        
        self.error_logger = setup_logger(
            f"pipeline.{pipeline_name}.errors",
            log_file=str(self.log_dir / f"{pipeline_name}_errors.log")
        )
        
        self.performance_logger = setup_logger(
            f"pipeline.{pipeline_name}.performance",
            log_file=str(self.log_dir / f"{pipeline_name}_performance.log")
        )
    
    def log_pipeline_start(self, config: Dict[str, Any]) -> None:
        """Log pipeline start with configuration."""
        self.main_logger.info(
            f"Pipeline {self.pipeline_name} started",
            extra={"extra_fields": {"event": "pipeline_start", "config": config}}
        )
    
    def log_pipeline_end(self, results: Dict[str, Any]) -> None:
        """Log pipeline completion with results."""
        self.main_logger.info(
            f"Pipeline {self.pipeline_name} completed",
            extra={"extra_fields": {"event": "pipeline_end", "results": results}}
        )
    
    def log_pipeline_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Log pipeline error with context."""
        self.error_logger.error(
            f"Pipeline {self.pipeline_name} failed: {str(error)}",
            extra={"extra_fields": {"event": "pipeline_error", "context": context}},
            exc_info=True
        )
    
    def log_stage_start(self, stage_name: str) -> None:
        """Log stage start."""
        self.main_logger.info(
            f"Stage {stage_name} started",
            extra={"extra_fields": {"event": "stage_start", "stage": stage_name}}
        )
    
    def log_stage_end(self, stage_name: str, stats: Dict[str, Any]) -> None:
        """Log stage completion with statistics."""
        self.main_logger.info(
            f"Stage {stage_name} completed",
            extra={"extra_fields": {"event": "stage_end", "stage": stage_name, "stats": stats}}
        )
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metrics."""
        self.performance_logger.info(
            f"Performance: {operation} took {duration:.2f}s",
            extra={"extra_fields": {"event": "performance", "operation": operation, "duration": duration, **kwargs}}
        )
    
    def log_data_quality(self, quality_metrics: Dict[str, Any]) -> None:
        """Log data quality metrics."""
        self.main_logger.info(
            "Data quality metrics",
            extra={"extra_fields": {"event": "data_quality", "metrics": quality_metrics}}
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {str(e)}")
            raise
    
    return wrapper


def log_execution_time(func):
    """Decorator to log function execution time."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"{func.__name__} executed in {duration:.2f} seconds")
            return result
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"{func.__name__} failed after {duration:.2f} seconds: {str(e)}")
            raise
    
    return wrapper 