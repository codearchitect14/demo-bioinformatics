"""
Download utilities for data pipeline system.

This module provides utilities for downloading data from various sources
including FTP, HTTP, and APIs with retry logic and progress tracking.
"""

import asyncio
import aiohttp
import aiofiles
import ftplib
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from urllib.parse import urlparse
import hashlib
import logging

from .logging_utils import setup_logger


class DownloadManager:
    """
    Manager for downloading data from various sources.
    
    Supports HTTP, HTTPS, FTP, and API downloads with retry logic,
    progress tracking, and integrity verification.
    """
    
    def __init__(self, max_retries: int = 3, timeout: int = 300):
        """
        Initialize download manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = setup_logger("download_manager")
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def download_file(
        self,
        url: str,
        destination: str,
        chunk_size: int = 8192,
        verify_checksum: bool = False,
        expected_checksum: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Download a file from URL.
        
        Args:
            url: Source URL
            destination: Destination file path
            chunk_size: Size of chunks to download
            verify_checksum: Whether to verify file checksum
            expected_checksum: Expected checksum value
            progress_callback: Callback function for progress updates
            
        Returns:
            Dictionary with download results
        """
        parsed_url = urlparse(url)
        
        if parsed_url.scheme in ['http', 'https']:
            return await self._download_http(url, destination, chunk_size, verify_checksum, expected_checksum, progress_callback)
        elif parsed_url.scheme == 'ftp':
            return await self._download_ftp(url, destination, chunk_size, verify_checksum, expected_checksum, progress_callback)
        else:
            raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")
    
    async def _download_http(
        self,
        url: str,
        destination: str,
        chunk_size: int,
        verify_checksum: bool,
        expected_checksum: Optional[str],
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Download file via HTTP/HTTPS."""
        if not self.session:
            raise RuntimeError("DownloadManager must be used as async context manager")
        
        start_time = time.time()
        downloaded_bytes = 0
        
        try:
            # Create destination directory
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                
                # Get file size for progress tracking
                total_size = int(response.headers.get('content-length', 0))
                
                async with aiofiles.open(destination, 'wb') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        await f.write(chunk)
                        downloaded_bytes += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded_bytes / total_size) * 100
                            progress_callback(progress, downloaded_bytes, total_size)
            
            # Verify checksum if requested
            if verify_checksum and expected_checksum:
                actual_checksum = await self._calculate_checksum(destination)
                if actual_checksum != expected_checksum:
                    raise ValueError(f"Checksum verification failed: expected {expected_checksum}, got {actual_checksum}")
            
            duration = time.time() - start_time
            speed = downloaded_bytes / duration if duration > 0 else 0
            
            self.logger.info(f"Downloaded {url} to {destination} ({downloaded_bytes} bytes, {speed:.2f} bytes/s)")
            
            return {
                "success": True,
                "url": url,
                "destination": destination,
                "bytes_downloaded": downloaded_bytes,
                "duration": duration,
                "speed_bytes_per_sec": speed
            }
            
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {str(e)}")
            return {
                "success": False,
                "url": url,
                "destination": destination,
                "error": str(e)
            }
    
    async def _download_ftp(
        self,
        url: str,
        destination: str,
        chunk_size: int,
        verify_checksum: bool,
        expected_checksum: Optional[str],
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Download file via FTP."""
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port or 21
        username = parsed_url.username or 'anonymous'
        password = parsed_url.password or 'anonymous@example.com'
        remote_path = parsed_url.path
        
        start_time = time.time()
        downloaded_bytes = 0
        
        try:
            # Create destination directory
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use asyncio to run FTP in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._download_ftp_sync,
                host, port, username, password, remote_path, destination,
                chunk_size, progress_callback
            )
            
            if result["success"]:
                downloaded_bytes = result["bytes_downloaded"]
                
                # Verify checksum if requested
                if verify_checksum and expected_checksum:
                    actual_checksum = await self._calculate_checksum(destination)
                    if actual_checksum != expected_checksum:
                        raise ValueError(f"Checksum verification failed: expected {expected_checksum}, got {actual_checksum}")
                
                duration = time.time() - start_time
                speed = downloaded_bytes / duration if duration > 0 else 0
                
                self.logger.info(f"Downloaded {url} to {destination} ({downloaded_bytes} bytes, {speed:.2f} bytes/s)")
                
                return {
                    "success": True,
                    "url": url,
                    "destination": destination,
                    "bytes_downloaded": downloaded_bytes,
                    "duration": duration,
                    "speed_bytes_per_sec": speed
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {str(e)}")
            return {
                "success": False,
                "url": url,
                "destination": destination,
                "error": str(e)
            }
    
    def _download_ftp_sync(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        remote_path: str,
        destination: str,
        chunk_size: int,
        progress_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """Synchronous FTP download."""
        try:
            with ftplib.FTP() as ftp:
                ftp.connect(host, port)
                ftp.login(username, password)
                
                # Get file size
                file_size = ftp.size(remote_path)
                
                downloaded_bytes = 0
                
                with open(destination, 'wb') as f:
                    def callback(data):
                        nonlocal downloaded_bytes
                        f.write(data)
                        downloaded_bytes += len(data)
                        
                        if progress_callback and file_size > 0:
                            progress = (downloaded_bytes / file_size) * 100
                            progress_callback(progress, downloaded_bytes, file_size)
                    
                    ftp.retrbinary(f'RETR {remote_path}', callback, blocksize=chunk_size)
                
                return {
                    "success": True,
                    "bytes_downloaded": downloaded_bytes
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_with_retry(
        self,
        url: str,
        destination: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Download file with retry logic.
        
        Args:
            url: Source URL
            destination: Destination file path
            **kwargs: Additional arguments for download_file
            
        Returns:
            Dictionary with download results
        """
        for attempt in range(self.max_retries):
            try:
                result = await self.download_file(url, destination, **kwargs)
                
                if result["success"]:
                    return result
                else:
                    self.logger.warning(f"Download attempt {attempt + 1} failed: {result.get('error')}")
                    
            except Exception as e:
                self.logger.warning(f"Download attempt {attempt + 1} failed: {str(e)}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt
                self.logger.info(f"Waiting {wait_time} seconds before retry")
                await asyncio.sleep(wait_time)
        
        # All retries failed
        return {
            "success": False,
            "url": url,
            "destination": destination,
            "error": f"All {self.max_retries} download attempts failed"
        }
    
    async def download_multiple_files(
        self,
        downloads: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Download multiple files concurrently.
        
        Args:
            downloads: List of download configurations
            max_concurrent: Maximum concurrent downloads
            
        Returns:
            List of download results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(download_config):
            async with semaphore:
                return await self.download_with_retry(**download_config)
        
        tasks = [download_with_semaphore(config) for config in downloads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "url": downloads[i].get("url", "unknown"),
                    "destination": downloads[i].get("destination", "unknown"),
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _calculate_checksum(self, file_path: str, algorithm: str = "md5") -> str:
        """Calculate file checksum."""
        hash_func = hashlib.new(algorithm)
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    async def check_file_exists(self, url: str) -> bool:
        """Check if file exists at URL."""
        if not self.session:
            raise RuntimeError("DownloadManager must be used as async context manager")
        
        try:
            async with self.session.head(url) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def get_file_info(self, url: str) -> Dict[str, Any]:
        """Get file information from URL."""
        if not self.session:
            raise RuntimeError("DownloadManager must be used as async context manager")
        
        try:
            async with self.session.head(url) as response:
                if response.status == 200:
                    return {
                        "exists": True,
                        "size": int(response.headers.get('content-length', 0)),
                        "last_modified": response.headers.get('last-modified'),
                        "content_type": response.headers.get('content-type'),
                        "etag": response.headers.get('etag')
                    }
                else:
                    return {"exists": False}
        except Exception as e:
            return {"exists": False, "error": str(e)}


class ProgressTracker:
    """Track download progress."""
    
    def __init__(self, total_files: int = 1):
        """
        Initialize progress tracker.
        
        Args:
            total_files: Total number of files to track
        """
        self.total_files = total_files
        self.completed_files = 0
        self.total_bytes = 0
        self.downloaded_bytes = 0
        self.start_time = time.time()
        self.logger = setup_logger("progress_tracker")
    
    def update_progress(self, progress: float, downloaded: int, total: int) -> None:
        """Update progress for current file."""
        self.downloaded_bytes = downloaded
        self.total_bytes = total
        
        # Log progress every 10%
        if int(progress) % 10 == 0:
            self.logger.info(f"Download progress: {progress:.1f}% ({downloaded}/{total} bytes)")
    
    def file_completed(self) -> None:
        """Mark a file as completed."""
        self.completed_files += 1
        overall_progress = (self.completed_files / self.total_files) * 100
        self.logger.info(f"File {self.completed_files}/{self.total_files} completed ({overall_progress:.1f}%)")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary."""
        duration = time.time() - self.start_time
        speed = self.downloaded_bytes / duration if duration > 0 else 0
        
        return {
            "completed_files": self.completed_files,
            "total_files": self.total_files,
            "downloaded_bytes": self.downloaded_bytes,
            "duration": duration,
            "speed_bytes_per_sec": speed,
            "overall_progress": (self.completed_files / self.total_files) * 100
        } 