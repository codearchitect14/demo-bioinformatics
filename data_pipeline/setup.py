#!/usr/bin/env python3
"""
Setup script for the data pipeline package.
"""

from setuptools import setup, find_packages

setup(
    name="genomics-data-pipeline",
    version="1.0.0",
    description="AI-Powered Genomics Platform Data Pipeline System",
    author="GenomicsAI Team",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "pyarrow>=12.0.0",
        "aiohttp>=3.8.0",
        "aiofiles>=23.0.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "asyncpg>=0.28.0",
        "pydantic>=2.0.0",
        "jsonschema>=4.17.0",
        "tqdm>=4.65.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "structlog>=23.0.0",
    ],
    python_requires=">=3.8",
) 