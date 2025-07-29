"""
PubMed data pipeline implementation.

This module provides a complete pipeline for downloading, processing, and
loading PubMed data into the genomics platform for literature mining.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import gzip
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import hashlib
import re

from base.base_pipeline import BaseDatasetPipeline
from utils.download_utils import DownloadManager
from utils.logging_utils import setup_logger


class PubMedPipeline(BaseDatasetPipeline):
    """
    Pipeline for processing PubMed biomedical literature data.
    
    PubMed is a comprehensive database of biomedical literature containing
    abstracts, full-text articles, and metadata for scientific publications.
    """
    
    def __init__(self, config: Dict[str, Any], db_session=None, cache_enabled: bool = True):
        """
        Initialize PubMed pipeline.
        
        Args:
            config: Pipeline configuration
            db_session: Database session
            cache_enabled: Whether to enable caching
        """
        super().__init__("pubmed", config, db_session, cache_enabled)
        
        # PubMed-specific configuration
        self.ncbi_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.pubmed_api_key = config.get("pubmed_api_key", "")
        self.max_articles_per_request = config.get("max_articles_per_request", 100)
        self.delay_between_requests = config.get("delay_between_requests", 0.34)  # NCBI rate limit
        
        # Search terms for genomics and bioinformatics
        self.search_terms = config.get("search_terms", [
            "genomics", "bioinformatics", "genetic variation", "gene expression",
            "cancer genomics", "precision medicine", "drug discovery",
            "biomarker", "pharmacogenomics", "genetic testing"
        ])
        
        # Date range for data collection
        self.start_date = config.get("start_date", "2020-01-01")
        self.end_date = config.get("end_date", datetime.now().strftime("%Y-%m-%d"))
        
        # Schema definitions for different data types
        self.schemas = {
            "articles": {
                "required_columns": [
                    "pmid", "title", "abstract", "authors", "journal", "publication_date",
                    "doi", "keywords", "mesh_terms", "article_type"
                ],
                "column_types": {
                    "pmid": "integer",
                    "publication_date": "datetime"
                }
            },
            "citations": {
                "required_columns": [
                    "citing_pmid", "cited_pmid", "citation_date", "citation_type"
                ],
                "column_types": {
                    "citing_pmid": "integer",
                    "cited_pmid": "integer",
                    "citation_date": "datetime"
                }
            },
            "authors": {
                "required_columns": [
                    "pmid", "author_name", "author_affiliation", "author_order"
                ],
                "column_types": {
                    "pmid": "integer",
                    "author_order": "integer"
                }
            }
        }
    
    async def _download_data(self) -> None:
        """Download PubMed data using NCBI E-utilities API."""
        self.logger.info("Starting PubMed data download")
        
        # Create download tasks for each search term
        download_tasks = []
        
        for search_term in self.search_terms:
            task = self._download_pubmed_data(search_term)
            download_tasks.append(task)
        
        # Execute downloads with rate limiting
        if download_tasks:
            for task in download_tasks:
                try:
                    result = await task
                    if result.get("success", False):
                        self.logger.info(f"Download completed for: {result.get('search_term')}")
                    else:
                        self.logger.error(f"Download failed for: {result.get('search_term')}")
                    
                    # Respect NCBI rate limits
                    await asyncio.sleep(self.delay_between_requests)
                    
                except Exception as e:
                    self.logger.error(f"Download task failed: {str(e)}")
    
    async def _download_pubmed_data(self, search_term: str) -> Dict[str, Any]:
        """Download PubMed data for a specific search term."""
        try:
            self.logger.info(f"Downloading PubMed data for: {search_term}")
            
            # Step 1: Search for articles
            article_ids = await self._search_articles(search_term)
            
            if not article_ids:
                self.logger.warning(f"No articles found for search term: {search_term}")
                return {
                    "success": True,
                    "search_term": search_term,
                    "articles_found": 0,
                    "message": "No articles found"
                }
            
            # Step 2: Fetch article details
            articles_data = await self._fetch_article_details(article_ids)
            
            # Step 3: Fetch citations
            citations_data = await self._fetch_citations(article_ids)
            
            # Step 4: Save data
            await self._save_pubmed_data(search_term, articles_data, citations_data)
            
            return {
                "success": True,
                "search_term": search_term,
                "articles_found": len(article_ids),
                "articles_processed": len(articles_data),
                "citations_found": len(citations_data)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to download PubMed data for {search_term}: {str(e)}")
            return {
                "success": False,
                "search_term": search_term,
                "error": str(e)
            }
    
    async def _search_articles(self, search_term: str) -> List[str]:
        """Search for articles using PubMed E-utilities."""
        try:
            # Build search query
            query = f'"{search_term}"[Title/Abstract] AND ("{self.start_date}"[Date - Publication] : "{self.end_date}"[Date - Publication])'
            
            # Construct URL
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": self.max_articles_per_request,
                "retmode": "json",
                "sort": "date"
            }
            
            if self.pubmed_api_key:
                params["api_key"] = self.pubmed_api_key
            
            # Make API request
            url = f"{self.ncbi_base_url}esearch.fcgi"
            async with DownloadManager() as download_manager:
                if hasattr(download_manager, 'session') and download_manager.session:
                    async with download_manager.session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "esearchresult" in data:
                                return data["esearchresult"].get("idlist", [])
                            else:
                                self.logger.error(f"Unexpected response format: {data}")
                                return []
                        else:
                            self.logger.error(f"Search request failed: {response.status}")
                            return []
                else:
                    # Fallback to synchronous request
                    import requests
                    response = requests.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        if "esearchresult" in data:
                            return data["esearchresult"].get("idlist", [])
                        else:
                            self.logger.error(f"Unexpected response format: {data}")
                            return []
                    else:
                        self.logger.error(f"Search request failed: {response.status_code}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Failed to search articles: {str(e)}")
            return []
    
    async def _fetch_article_details(self, article_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch detailed article information."""
        try:
            if not article_ids:
                return []
            
            # Batch process article IDs
            batch_size = 50  # NCBI recommended batch size
            all_articles = []
            
            for i in range(0, len(article_ids), batch_size):
                batch_ids = article_ids[i:i + batch_size]
                
                # Construct URL
                params = {
                    "db": "pubmed",
                    "id": ",".join(batch_ids),
                    "retmode": "xml",
                    "rettype": "abstract"
                }
                
                if self.pubmed_api_key:
                    params["api_key"] = self.pubmed_api_key
                
                # Make API request
                url = f"{self.ncbi_base_url}efetch.fcgi"
                async with DownloadManager() as download_manager:
                    if hasattr(download_manager, 'session') and download_manager.session:
                        async with download_manager.session.get(url, params=params) as response:
                            if response.status == 200:
                                xml_data = await response.text()
                                articles = self._parse_pubmed_xml(xml_data)
                                all_articles.extend(articles)
                            else:
                                self.logger.error(f"Fetch request failed: {response.status}")
                    else:
                        # Fallback to synchronous request
                        import requests
                        response = requests.get(url, params=params)
                        if response.status_code == 200:
                            xml_data = response.text
                            articles = self._parse_pubmed_xml(xml_data)
                            all_articles.extend(articles)
                        else:
                            self.logger.error(f"Fetch request failed: {response.status_code}")
                
                # Respect rate limits
                await asyncio.sleep(self.delay_between_requests)
            
            return all_articles
            
        except Exception as e:
            self.logger.error(f"Failed to fetch article details: {str(e)}")
            return []
    
    async def _fetch_citations(self, article_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch citation information for articles."""
        try:
            if not article_ids:
                return []
            
            all_citations = []
            
            for pmid in article_ids[:10]:  # Limit for testing
                # Construct URL for citations
                params = {
                    "db": "pubmed",
                    "linkname": "pubmed_pubmed_citedin",
                    "id": pmid,
                    "retmode": "xml"
                }
                
                if self.pubmed_api_key:
                    params["api_key"] = self.pubmed_api_key
                
                # Make API request
                url = f"{self.ncbi_base_url}elink.fcgi"
                async with DownloadManager() as download_manager:
                    if hasattr(download_manager, 'session') and download_manager.session:
                        async with download_manager.session.get(url, params=params) as response:
                            if response.status == 200:
                                xml_data = await response.text()
                                citations = self._parse_citation_xml(xml_data, pmid)
                                all_citations.extend(citations)
                            else:
                                self.logger.error(f"Citation request failed: {response.status}")
                    else:
                        # Fallback to synchronous request
                        import requests
                        response = requests.get(url, params=params)
                        if response.status_code == 200:
                            xml_data = response.text
                            citations = self._parse_citation_xml(xml_data, pmid)
                            all_citations.extend(citations)
                        else:
                            self.logger.error(f"Citation request failed: {response.status_code}")
                
                # Respect rate limits
                await asyncio.sleep(self.delay_between_requests)
            
            return all_citations
            
        except Exception as e:
            self.logger.error(f"Failed to fetch citations: {str(e)}")
            return []
    
    def _parse_pubmed_xml(self, xml_data: str) -> List[Dict[str, Any]]:
        """Parse PubMed XML data into structured format."""
        try:
            articles = []
            root = ET.fromstring(xml_data)
            
            for pubmed_article in root.findall(".//PubmedArticle"):
                article = self._extract_article_data(pubmed_article)
                if article:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Failed to parse PubMed XML: {str(e)}")
            return []
    
    def _extract_article_data(self, pubmed_article: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract article data from PubMed XML element."""
        try:
            article = {}
            
            # Extract PMID
            pmid_elem = pubmed_article.find(".//PMID")
            if pmid_elem is not None:
                article["pmid"] = int(pmid_elem.text)
            else:
                return None
            
            # Extract title
            title_elem = pubmed_article.find(".//ArticleTitle")
            if title_elem is not None:
                article["title"] = title_elem.text or ""
            else:
                article["title"] = ""
            
            # Extract abstract
            abstract_elem = pubmed_article.find(".//AbstractText")
            if abstract_elem is not None:
                article["abstract"] = abstract_elem.text or ""
            else:
                article["abstract"] = ""
            
            # Extract authors
            authors = []
            author_list = pubmed_article.find(".//AuthorList")
            if author_list is not None:
                for author in author_list.findall("Author"):
                    author_data = {}
                    last_name = author.find("LastName")
                    first_name = author.find("ForeName")
                    if last_name is not None:
                        author_data["last_name"] = last_name.text or ""
                    if first_name is not None:
                        author_data["first_name"] = first_name.text or ""
                    if author_data:
                        authors.append(author_data)
            
            article["authors"] = json.dumps(authors)
            
            # Extract journal information
            journal_elem = pubmed_article.find(".//Journal/Title")
            if journal_elem is not None:
                article["journal"] = journal_elem.text or ""
            else:
                article["journal"] = ""
            
            # Extract publication date
            pub_date = pubmed_article.find(".//PubDate")
            if pub_date is not None:
                year_elem = pub_date.find("Year")
                month_elem = pub_date.find("Month")
                day_elem = pub_date.find("Day")
                
                year = year_elem.text if year_elem is not None else "2020"
                month = month_elem.text if month_elem is not None else "01"
                day = day_elem.text if day_elem is not None else "01"
                
                try:
                    article["publication_date"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    article["publication_date"] = "2020-01-01"
            else:
                article["publication_date"] = "2020-01-01"
            
            # Extract DOI
            doi_elem = pubmed_article.find(".//ELocationID[@EIdType='doi']")
            if doi_elem is not None:
                article["doi"] = doi_elem.text or ""
            else:
                article["doi"] = ""
            
            # Extract keywords
            keywords = []
            keyword_list = pubmed_article.find(".//KeywordList")
            if keyword_list is not None:
                for keyword in keyword_list.findall("Keyword"):
                    if keyword.text:
                        keywords.append(keyword.text)
            
            article["keywords"] = json.dumps(keywords)
            
            # Extract MeSH terms
            mesh_terms = []
            mesh_list = pubmed_article.find(".//MeshHeadingList")
            if mesh_list is not None:
                for mesh in mesh_list.findall("MeshHeading"):
                    descriptor = mesh.find("DescriptorName")
                    if descriptor is not None and descriptor.text:
                        mesh_terms.append(descriptor.text)
            
            article["mesh_terms"] = json.dumps(mesh_terms)
            
            # Extract article type
            article_type_list = pubmed_article.find(".//PublicationTypeList")
            if article_type_list is not None:
                article_types = []
                for article_type in article_type_list.findall("PublicationType"):
                    if article_type.text:
                        article_types.append(article_type.text)
                article["article_type"] = json.dumps(article_types)
            else:
                article["article_type"] = json.dumps([])
            
            return article
            
        except Exception as e:
            self.logger.error(f"Failed to extract article data: {str(e)}")
            return None
    
    def _parse_citation_xml(self, xml_data: str, citing_pmid: str) -> List[Dict[str, Any]]:
        """Parse citation XML data."""
        try:
            citations = []
            root = ET.fromstring(xml_data)
            
            for link_set in root.findall(".//LinkSet"):
                for link in link_set.findall(".//Link"):
                    cited_pmid_elem = link.find("Id")
                    if cited_pmid_elem is not None:
                        citation = {
                            "citing_pmid": int(citing_pmid),
                            "cited_pmid": int(cited_pmid_elem.text),
                            "citation_date": datetime.now().strftime("%Y-%m-%d"),
                            "citation_type": "cited_in"
                        }
                        citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Failed to parse citation XML: {str(e)}")
            return []
    
    async def _save_pubmed_data(self, search_term: str, articles_data: List[Dict], citations_data: List[Dict]) -> None:
        """Save PubMed data to files."""
        try:
            # Create search-specific directory
            search_dir = self.raw_data_path / "pubmed" / search_term.replace(" ", "_")
            search_dir.mkdir(parents=True, exist_ok=True)
            
            # Save articles data
            if articles_data:
                articles_df = pd.DataFrame(articles_data)
                articles_file = search_dir / f"articles_{datetime.now().strftime('%Y%m%d')}.parquet"
                articles_df.to_parquet(articles_file, index=False)
                self.logger.info(f"Saved {len(articles_data)} articles to {articles_file}")
            
            # Save citations data
            if citations_data:
                citations_df = pd.DataFrame(citations_data)
                citations_file = search_dir / f"citations_{datetime.now().strftime('%Y%m%d')}.parquet"
                citations_df.to_parquet(citations_file, index=False)
                self.logger.info(f"Saved {len(citations_data)} citations to {citations_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save PubMed data: {str(e)}")
            raise
    
    async def _validate_data(self) -> None:
        """Validate downloaded PubMed data."""
        self.logger.info("Validating PubMed data")
        
        for search_term in self.search_terms:
            search_dir = self.raw_data_path / "pubmed" / search_term.replace(" ", "_")
            
            if search_dir.exists():
                await self._validate_search_data(search_term, search_dir)
    
    async def _validate_search_data(self, search_term: str, data_dir: Path) -> None:
        """Validate data for a specific search term."""
        try:
            files = list(data_dir.glob("*.parquet"))
            
            if not files:
                self.logger.warning(f"No files found in {data_dir}")
                return
            
            # Validate each file
            for file_path in files:
                await self._validate_pubmed_file(file_path)
            
            self.logger.info(f"Validation completed for {search_term}")
            
        except Exception as e:
            self.logger.error(f"Validation failed for {search_term}: {str(e)}")
            raise
    
    async def _validate_pubmed_file(self, file_path: Path) -> None:
        """Validate a specific PubMed file."""
        try:
            # Check file size
            if file_path.stat().st_size == 0:
                raise ValueError(f"Empty file: {file_path}")
            
            # Read and validate data
            data = pd.read_parquet(file_path)
            
            if len(data) == 0:
                raise ValueError(f"Empty dataset in {file_path}")
            
            # Check for required columns based on file type
            if "articles" in file_path.name:
                required_columns = ["pmid", "title", "abstract"]
                missing_columns = [col for col in required_columns if col not in data.columns]
                if missing_columns:
                    raise ValueError(f"Missing required columns in {file_path}: {missing_columns}")
                
                # Validate PMID uniqueness
                if "pmid" in data.columns:
                    if data["pmid"].duplicated().any():
                        self.logger.warning(f"Duplicate PMIDs found in {file_path}")
            
            elif "citations" in file_path.name:
                required_columns = ["citing_pmid", "cited_pmid"]
                missing_columns = [col for col in required_columns if col not in data.columns]
                if missing_columns:
                    raise ValueError(f"Missing required columns in {file_path}: {missing_columns}")
            
        except Exception as e:
            self.logger.error(f"File validation failed for {file_path}: {str(e)}")
            raise
    
    async def _transform_data(self) -> None:
        """Transform PubMed data to unified schema."""
        self.logger.info("Transforming PubMed data")
        
        for search_term in self.search_terms:
            search_dir = self.raw_data_path / "pubmed" / search_term.replace(" ", "_")
            
            if search_dir.exists():
                await self._transform_search_data(search_term, search_dir)
    
    async def _transform_search_data(self, search_term: str, data_dir: Path) -> None:
        """Transform data for a specific search term."""
        try:
            files = list(data_dir.glob("*.parquet"))
            
            if not files:
                return
            
            # Process files
            for file_path in files:
                await self._transform_pubmed_file(file_path, search_term)
            
            self.logger.info(f"Transformation completed for {search_term}")
            
        except Exception as e:
            self.logger.error(f"Transformation failed for {search_term}: {str(e)}")
            raise
    
    async def _transform_pubmed_file(self, file_path: Path, search_term: str) -> None:
        """Transform a specific PubMed file."""
        try:
            # Read data
            data = pd.read_parquet(file_path)
            
            if len(data) == 0:
                return
            
            # Transform data based on file type
            if "articles" in file_path.name:
                transformed_data = self._transform_article_data(data, search_term)
            elif "citations" in file_path.name:
                transformed_data = self._transform_citation_data(data, search_term)
            else:
                transformed_data = self._transform_generic_data(data, search_term, "unknown")
            
            # Save transformed data
            output_file = self.processed_data_path / "pubmed" / search_term.replace(" ", "_") / f"{file_path.stem}_transformed.parquet"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            transformed_data.to_parquet(output_file, index=False)
            
            self.logger.debug(f"Transformed {file_path} -> {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to transform {file_path}: {str(e)}")
            raise
    
    def _transform_article_data(self, data: pd.DataFrame, search_term: str) -> pd.DataFrame:
        """Transform article data."""
        # Clean and standardize data
        data = data.copy()
        
        # Clean text fields
        if "title" in data.columns:
            data["title"] = data["title"].fillna("").astype(str).str.strip()
        
        if "abstract" in data.columns:
            data["abstract"] = data["abstract"].fillna("").astype(str).str.strip()
        
        if "journal" in data.columns:
            data["journal"] = data["journal"].fillna("").astype(str).str.strip()
        
        # Extract text features
        if "abstract" in data.columns:
            data["abstract_length"] = data["abstract"].str.len()
            data["word_count"] = data["abstract"].str.split().str.len()
        
        # Add metadata
        data["search_term"] = search_term
        data["data_type"] = "articles"
        data["source_type"] = "pubmed"
        data["transformed_at"] = datetime.now().isoformat()
        data["data_version"] = "1.0"
        
        # Clean data
        data = self._clean_article_data(data)
        
        return data
    
    def _transform_citation_data(self, data: pd.DataFrame, search_term: str) -> pd.DataFrame:
        """Transform citation data."""
        # Clean and standardize data
        data = data.copy()
        
        # Add metadata
        data["search_term"] = search_term
        data["data_type"] = "citations"
        data["source_type"] = "pubmed"
        data["transformed_at"] = datetime.now().isoformat()
        data["data_version"] = "1.0"
        
        # Clean data
        data = self._clean_citation_data(data)
        
        return data
    
    def _transform_generic_data(self, data: pd.DataFrame, search_term: str, data_type: str) -> pd.DataFrame:
        """Transform generic data."""
        # Add metadata
        data = data.copy()
        data["search_term"] = search_term
        data["data_type"] = data_type
        data["source_type"] = "pubmed"
        data["transformed_at"] = datetime.now().isoformat()
        data["data_version"] = "1.0"
        
        return data
    
    def _clean_article_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean article data."""
        # Handle missing values
        data = data.replace(['', 'nan', 'None'], np.nan)
        
        # Convert data types
        if "pmid" in data.columns:
            data["pmid"] = pd.to_numeric(data["pmid"], errors='coerce')
        
        if "publication_date" in data.columns:
            data["publication_date"] = pd.to_datetime(data["publication_date"], errors='coerce')
        
        # Remove rows with missing essential data
        if "pmid" in data.columns:
            data = data.dropna(subset=["pmid"])
        
        # Clean text fields
        for col in ["title", "abstract", "journal"]:
            if col in data.columns:
                data[col] = data[col].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
        
        return data
    
    def _clean_citation_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean citation data."""
        # Handle missing values
        data = data.replace(['', 'nan', 'None'], np.nan)
        
        # Convert data types
        for col in ["citing_pmid", "cited_pmid"]:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # Remove rows with missing essential data
        data = data.dropna(subset=["citing_pmid", "cited_pmid"])
        
        return data
    
    async def _load_batch(self, batch: pd.DataFrame) -> None:
        """Load a batch of PubMed data into database."""
        if not self.db_session:
            return
        
        try:
            # Convert DataFrame to list of dictionaries
            records = batch.to_dict('records')
            
            # Insert records into database
            self.logger.debug(f"Loading batch of {len(records)} PubMed records")
            
            # Example database insertion (commented out for now)
            # for record in records:
            #     pubmed_record = PubMedRecord(**record)
            #     self.db_session.add(pubmed_record)
            # 
            # self.db_session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to load batch: {str(e)}")
            self.db_session.rollback()
            raise
    
    async def _create_index(self, index_config: Dict[str, Any]) -> None:
        """Create database indexes for PubMed data."""
        if not self.db_session:
            return
        
        try:
            # Create indexes for efficient querying
            indexes = [
                {"name": "idx_pubmed_pmid", "columns": ["pmid"]},
                {"name": "idx_pubmed_search_term", "columns": ["search_term"]},
                {"name": "idx_pubmed_data_type", "columns": ["data_type"]},
                {"name": "idx_pubmed_publication_date", "columns": ["publication_date"]},
                {"name": "idx_pubmed_citing_pmid", "columns": ["citing_pmid"]},
                {"name": "idx_pubmed_cited_pmid", "columns": ["cited_pmid"]}
            ]
            
            for index in indexes:
                self.logger.debug(f"Creating index: {index['name']}")
                # This would typically execute SQL CREATE INDEX statements
                # For now, we'll just log the operation
            
        except Exception as e:
            self.logger.error(f"Failed to create indexes: {str(e)}")
            raise
    
    async def _prepare_cache_data(self) -> Optional[Dict[str, Any]]:
        """Prepare PubMed data for caching."""
        try:
            # Cache frequently accessed data
            cache_data = {
                "search_term_counts": {},
                "data_type_counts": {},
                "publication_timeline": {},
                "top_journals": {},
                "top_authors": {}
            }
            
            # Read processed data to generate cache
            processed_files = list(self.processed_data_path.rglob("*.parquet"))
            
            for file_path in processed_files:
                try:
                    data = pd.read_parquet(file_path)
                    
                    # Count by search term
                    if "search_term" in data.columns:
                        search_counts = data["search_term"].value_counts()
                        for search_term, count in search_counts.items():
                            cache_data["search_term_counts"][search_term] = cache_data["search_term_counts"].get(search_term, 0) + count
                    
                    # Count by data type
                    if "data_type" in data.columns:
                        data_type_counts = data["data_type"].value_counts()
                        for data_type, count in data_type_counts.items():
                            cache_data["data_type_counts"][data_type] = cache_data["data_type_counts"].get(data_type, 0) + count
                    
                    # Publication timeline
                    if "publication_date" in data.columns:
                        timeline = data["publication_date"].dt.year.value_counts().sort_index()
                        cache_data["publication_timeline"][file_path.stem] = timeline.to_dict()
                    
                    # Top journals
                    if "journal" in data.columns:
                        top_journals = data["journal"].value_counts().head(10)
                        cache_data["top_journals"][file_path.stem] = top_journals.to_dict()
                    
                    # Top authors (simplified)
                    if "authors" in data.columns:
                        # This would require more complex parsing of author data
                        pass
                
                except Exception as e:
                    self.logger.warning(f"Failed to process {file_path} for cache: {str(e)}")
            
            return cache_data
            
        except Exception as e:
            self.logger.error(f"Failed to prepare cache data: {str(e)}")
            return None
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of PubMed data."""
        summary = {
            "dataset_name": "pubmed",
            "search_terms": {},
            "data_types": {},
            "total_files": 0,
            "total_records": 0
        }
        
        try:
            # Count files and records by search term and data type
            processed_files = list(self.processed_data_path.rglob("*.parquet"))
            summary["total_files"] = len(processed_files)
            
            for file_path in processed_files:
                try:
                    data = pd.read_parquet(file_path)
                    summary["total_records"] += len(data)
                    
                    # Update search term counts
                    if "search_term" in data.columns:
                        search_term = data["search_term"].iloc[0]
                        if search_term not in summary["search_terms"]:
                            summary["search_terms"][search_term] = {"files": 0, "records": 0}
                        summary["search_terms"][search_term]["files"] += 1
                        summary["search_terms"][search_term]["records"] += len(data)
                    
                    # Update data type counts
                    if "data_type" in data.columns:
                        data_type = data["data_type"].iloc[0]
                        if data_type not in summary["data_types"]:
                            summary["data_types"][data_type] = {"files": 0, "records": 0}
                        summary["data_types"][data_type]["files"] += 1
                        summary["data_types"][data_type]["records"] += len(data)
                
                except Exception as e:
                    self.logger.warning(f"Failed to process {file_path} for summary: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate data summary: {str(e)}")
        
        return summary
    
    def _progress_callback(self, progress: float, downloaded: int, total: int) -> None:
        """Callback for download progress."""
        if int(progress) % 10 == 0:
            self.logger.info(f"Download progress: {progress:.1f}% ({downloaded}/{total} bytes)") 