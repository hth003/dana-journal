"""
AI Model Download Manager

Handles downloading and managing the Qwen2.5-3B-Instruct model for local AI insights.
Uses huggingface-hub to download GGUF models to ~/.dana_journal/models/ directory.
"""

import sys
import time
import shutil
import os
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import threading
from dataclasses import dataclass

import psutil
import requests
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError


@dataclass
class DownloadProgress:
    """Download progress information."""

    bytes_downloaded: int = 0
    total_bytes: int = 0
    download_speed: float = 0.0  # bytes per second
    eta_seconds: Optional[int] = None
    status: str = (
        "initializing"  # "initializing", "downloading", "validating", "complete", "error"
    )
    error_message: Optional[str] = None


class ModelDownloadManager:
    """Manages AI model downloading with progress tracking and error handling."""

    # Model configuration
    MODEL_REPO = "Qwen/Qwen2.5-3B-Instruct-GGUF"
    MODEL_FILENAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
    MODEL_SIZE_BYTES = 2_200_000_000  # Approximately 2.1GB

    # Known file hash for validation (SHA256)
    EXPECTED_HASH = None  # We'll validate by size and basic integrity checks

    def __init__(self):
        self.models_dir = Path.home() / ".dana_journal" / "models"
        self.model_path = self.models_dir / self.MODEL_FILENAME
        self.temp_path = self.models_dir / f"{self.MODEL_FILENAME}.tmp"
        self.progress = DownloadProgress()
        self.download_thread: Optional[threading.Thread] = None
        self.cancel_requested = False

        # Create models directory
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def is_model_available(self, retry_count: int = 3) -> bool:
        """Check if the model is already downloaded and valid with retry logic for packaged apps."""
        for attempt in range(retry_count):
            try:
                if not self.model_path.exists():
                    if attempt < retry_count - 1:
                        # Brief delay for file system to settle in packaged environments
                        import time
                        time.sleep(0.1 * (attempt + 1))
                        continue
                    return False

                # Check file size is reasonable (at least 1GB, not more than 3GB)
                file_size = self.model_path.stat().st_size
                if file_size < 1_000_000_000 or file_size > 3_000_000_000:
                    if attempt < retry_count - 1:
                        import time
                        time.sleep(0.1 * (attempt + 1))
                        continue
                    return False

                # Basic validation - try to read the first few bytes
                with open(self.model_path, "rb") as f:
                    header = f.read(4)
                    # GGUF files start with 'GGUF' magic bytes
                    if header != b"GGUF":
                        if attempt < retry_count - 1:
                            import time
                            time.sleep(0.1 * (attempt + 1))
                            continue
                        return False

                return True
                
            except (OSError, IOError, PermissionError) as e:
                # Add more specific error handling for packaged apps
                if attempt < retry_count - 1:
                    import time
                    time.sleep(0.2 * (attempt + 1))  # Longer delay for file access issues
                    continue
                # Log the error for debugging in packaged environments
                print(f"Model validation failed after {retry_count} attempts: {e}")
                return False
        
        return False

    def get_model_path(self) -> Optional[Path]:
        """Get the path to the downloaded model file with enhanced validation."""
        # Use enhanced validation with retries
        if self.is_model_available(retry_count=5):  # More retries for path resolution
            return self.model_path
        return None
    
    def validate_model_path_for_packaged_app(self) -> Dict[str, Any]:
        """Enhanced validation specifically for packaged app environments."""
        validation_info = {
            "path_exists": False,
            "path_readable": False,
            "file_size_valid": False,
            "header_valid": False,
            "validation_successful": False,
            "error_message": None,
            "file_path": str(self.model_path),
            "parent_dir_exists": self.models_dir.exists(),
        }
        
        try:
            # Check if path exists with multiple attempts
            for attempt in range(5):
                if self.model_path.exists():
                    validation_info["path_exists"] = True
                    break
                import time
                time.sleep(0.1 * (attempt + 1))
            
            if not validation_info["path_exists"]:
                validation_info["error_message"] = "Model file does not exist"
                return validation_info
            
            # Check readability
            try:
                with open(self.model_path, "rb") as f:
                    f.read(1)  # Try to read one byte
                validation_info["path_readable"] = True
            except (OSError, IOError, PermissionError) as e:
                validation_info["error_message"] = f"Model file not readable: {e}"
                return validation_info
            
            # Check file size
            file_size = self.model_path.stat().st_size
            if 1_000_000_000 <= file_size <= 3_000_000_000:
                validation_info["file_size_valid"] = True
            else:
                validation_info["error_message"] = f"Invalid file size: {file_size} bytes"
                return validation_info
            
            # Check GGUF header
            with open(self.model_path, "rb") as f:
                header = f.read(4)
                if header == b"GGUF":
                    validation_info["header_valid"] = True
                else:
                    validation_info["error_message"] = f"Invalid GGUF header: {header}"
                    return validation_info
            
            validation_info["validation_successful"] = True
            
        except Exception as e:
            validation_info["error_message"] = f"Validation error: {e}"
        
        return validation_info

    def check_system_requirements(self) -> Dict[str, Any]:
        """Check if system meets requirements for model download and usage."""
        requirements = {
            "meets_requirements": True,
            "issues": [],
            "disk_space_gb": 0,
            "available_memory_gb": 0,
            "python_version": sys.version_info[:2],
        }

        try:
            # Check available disk space
            disk_usage = shutil.disk_usage(self.models_dir.parent)
            available_gb = disk_usage.free / (1024**3)
            requirements["disk_space_gb"] = round(available_gb, 1)

            if available_gb < 3.0:  # Need at least 3GB for download + temp files
                requirements["meets_requirements"] = False
                requirements["issues"].append(
                    f"Insufficient disk space. Need at least 3GB, have {available_gb:.1f}GB available."
                )

            # Check available memory
            memory = psutil.virtual_memory()
            available_memory_gb = memory.available / (1024**3)
            requirements["available_memory_gb"] = round(available_memory_gb, 1)

            if available_memory_gb < 2.0:  # Recommend at least 2GB for model loading
                requirements["issues"].append(
                    f"Low available memory. Recommend at least 2GB, have {available_memory_gb:.1f}GB available."
                )

            # Check Python version (need 3.11+)
            if sys.version_info < (3, 11):
                requirements["meets_requirements"] = False
                requirements["issues"].append(
                    f"Python 3.11+ required, have {sys.version_info[0]}.{sys.version_info[1]}"
                )

        except Exception as e:
            requirements["meets_requirements"] = False
            requirements["issues"].append(
                f"Error checking system requirements: {str(e)}"
            )

        return requirements

    def download_model_async(
        self, progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> None:
        """Start model download in a background thread."""
        if self.download_thread and self.download_thread.is_alive():
            return  # Download already in progress

        self.cancel_requested = False
        self.progress = DownloadProgress()

        def download_worker():
            self._download_model_sync(progress_callback)

        self.download_thread = threading.Thread(target=download_worker, daemon=True)
        self.download_thread.start()

    def cancel_download(self) -> None:
        """Cancel the current download."""
        self.cancel_requested = True

        # Clean up temp file
        if self.temp_path.exists():
            try:
                self.temp_path.unlink()
            except OSError:
                pass

        self.progress.status = "error"
        self.progress.error_message = "Download cancelled by user"

    def _download_model_sync(
        self, progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> None:
        """Synchronous model download with progress tracking."""

        def update_progress():
            if progress_callback:
                progress_callback(self.progress)

        try:
            self.progress.status = "initializing"
            update_progress()

            # Clean up any existing temp file
            if self.temp_path.exists():
                self.temp_path.unlink()

            # Custom download with progress tracking
            self.progress.status = "downloading"
            self.progress.total_bytes = self.MODEL_SIZE_BYTES
            update_progress()

            # Download using huggingface_hub with custom progress
            downloaded_file = self._download_with_progress(update_progress)

            if self.cancel_requested:
                return

            # Validate downloaded file
            self.progress.status = "validating"
            update_progress()

            if not self._validate_downloaded_file(downloaded_file):
                self.progress.status = "error"
                self.progress.error_message = "Downloaded file failed validation"
                update_progress()
                return

            # Move temp file to final location
            if downloaded_file != self.model_path:
                shutil.move(str(downloaded_file), str(self.model_path))

            self.progress.status = "complete"
            self.progress.bytes_downloaded = self.progress.total_bytes
            update_progress()

        except HfHubHTTPError as e:
            if "404" in str(e):
                self.progress.error_message = (
                    "Model not found. Please check your internet connection."
                )
            else:
                self.progress.error_message = f"Download failed: {str(e)}"
            self.progress.status = "error"
            update_progress()
        except RepositoryNotFoundError:
            self.progress.error_message = (
                "Model repository not found. The model may have moved."
            )
            self.progress.status = "error"
            update_progress()
        except Exception as e:
            self.progress.error_message = f"Unexpected error: {str(e)}"
            self.progress.status = "error"
            update_progress()
        finally:
            # Clean up temp files
            if self.temp_path.exists():
                try:
                    self.temp_path.unlink()
                except OSError:
                    pass

    def _download_with_progress(self, progress_callback: Callable) -> Path:
        """Download file with progress tracking."""
        # Use direct download by default for better progress tracking
        try:
            return self._download_direct_with_progress(progress_callback)
        except Exception as e:
            print(f"Direct download failed: {e}")
            # Fallback to hf_hub_download
            try:
                # Use hf_hub_download with a local cache directory
                cache_dir = self.models_dir / "cache"
                cache_dir.mkdir(exist_ok=True)

                # Download the file
                downloaded_path = hf_hub_download(
                    repo_id=self.MODEL_REPO,
                    filename=self.MODEL_FILENAME,
                    cache_dir=str(cache_dir),
                    local_dir=str(self.models_dir),
                    local_dir_use_symlinks=False,
                    resume_download=True,
                )

                # Since hf_hub_download doesn't provide progress callbacks,
                # we'll monitor the file size during download
                target_path = Path(downloaded_path)
                if target_path.exists():
                    self.progress.bytes_downloaded = target_path.stat().st_size
                    self.progress.total_bytes = max(
                        self.progress.total_bytes, self.progress.bytes_downloaded
                    )
                    progress_callback()

                return target_path

            except Exception as e2:
                raise Exception(
                    f"Both download methods failed. Direct: {e}, HF Hub: {e2}"
                )

    def _download_direct_with_progress(self, progress_callback: Callable) -> Path:
        """Optimized direct download with requests for better performance and diagnostics."""
        # Construct download URL
        url = f"https://huggingface.co/{self.MODEL_REPO}/resolve/main/{self.MODEL_FILENAME}"

        start_time = time.time()
        last_update_time = start_time
        
        # Dynamic chunk sizing - start with 1MB, can adjust based on performance
        initial_chunk_size = 1024 * 1024  # 1MB chunks
        chunk_size = initial_chunk_size
        UPDATE_INTERVAL = 3.0  # Update UI every 3 seconds instead of 0.5s
        
        # Performance tracking for diagnostics
        speed_samples = []
        optimal_chunk_size = initial_chunk_size

        try:
            # Create a session for connection pooling and keep-alive
            session = requests.Session()
            
            # Optimize session configuration
            session.headers.update({
                'User-Agent': 'Dana-Journal/1.0 (https://github.com/dana-team/dana-journal)',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            })
            
            # Configure adapter for better performance
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=1,
                pool_maxsize=1
            )
            session.mount("https://", adapter)
            session.mount("http://", adapter)

            # Use optimized timeout settings
            response = session.get(url, stream=True, timeout=(30, 300))  # (connect, read)
            response.raise_for_status()

            # Get total size from headers
            total_size = int(
                response.headers.get("content-length", self.MODEL_SIZE_BYTES)
            )
            self.progress.total_bytes = total_size

            # Download with adaptive chunking, reduced UI updates, and performance monitoring
            with open(self.temp_path, "wb") as f:
                bytes_downloaded = 0
                chunks_written = 0
                chunk_start_time = time.time()

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.cancel_requested:
                        raise InterruptedError("Download cancelled")

                    if chunk:
                        chunk_write_start = time.time()
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        chunks_written += 1
                        chunk_write_time = time.time() - chunk_write_start

                        # Update progress much less frequently (every 3 seconds)
                        current_time = time.time()
                        if current_time - last_update_time > UPDATE_INTERVAL:
                            self.progress.bytes_downloaded = bytes_downloaded

                            # Calculate download speed and collect performance data
                            time_elapsed = current_time - start_time
                            if time_elapsed > 0:
                                current_speed = bytes_downloaded / time_elapsed
                                self.progress.download_speed = current_speed
                                
                                # Collect speed samples for adaptive chunk sizing
                                if len(speed_samples) < 10:  # Collect first 10 samples
                                    speed_samples.append(current_speed)
                                
                                # Adaptive chunk sizing after collecting some samples
                                if len(speed_samples) >= 5 and chunks_written % 50 == 0:
                                    avg_speed = sum(speed_samples[-5:]) / 5  # Average of last 5 samples
                                    
                                    # Adjust chunk size based on performance
                                    if avg_speed < 1024 * 1024:  # Less than 1MB/s - reduce chunk size
                                        chunk_size = max(256 * 1024, chunk_size // 2)  # Min 256KB
                                    elif avg_speed > 5 * 1024 * 1024:  # More than 5MB/s - increase chunk size
                                        chunk_size = min(8 * 1024 * 1024, chunk_size * 2)  # Max 8MB

                                # Estimate time remaining
                                remaining_bytes = total_size - bytes_downloaded
                                if self.progress.download_speed > 0:
                                    self.progress.eta_seconds = int(
                                        remaining_bytes / self.progress.download_speed
                                    )

                            progress_callback()
                            last_update_time = current_time
                            
                        # Flush file buffer periodically but not too frequently
                        if chunks_written % 200 == 0:  # Every ~200MB at 1MB chunks
                            f.flush()
                            os.fsync(f.fileno())  # Force write to disk
                            
                        # Log performance issues for debugging
                        if chunk_write_time > 1.0:  # If writing a chunk takes more than 1 second
                            # This could indicate disk I/O issues in packaged apps
                            pass  # Could write to diagnostic file here

            # Final progress update
            self.progress.bytes_downloaded = bytes_downloaded
            progress_callback()
            
            # Close session to clean up connections
            session.close()

            return self.temp_path

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error during download: {str(e)}")
        except Exception as e:
            if self.temp_path.exists():
                self.temp_path.unlink()
            raise e

    def _validate_downloaded_file(self, file_path: Path) -> bool:
        """Validate the downloaded model file."""
        try:
            if not file_path.exists():
                return False

            # Check file size is reasonable
            file_size = file_path.stat().st_size
            if file_size < 1_000_000_000:  # Less than 1GB is probably corrupted
                return False

            # Check GGUF magic bytes
            with open(file_path, "rb") as f:
                header = f.read(4)
                if header != b"GGUF":
                    return False

            # File appears valid
            return True

        except Exception:
            return False

    def remove_model(self) -> bool:
        """Remove the downloaded model file."""
        try:
            if self.model_path.exists():
                self.model_path.unlink()

            # Also clean up cache directory
            cache_dir = self.models_dir / "cache"
            if cache_dir.exists():
                shutil.rmtree(cache_dir, ignore_errors=True)

            return True
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model."""
        info = {
            "model_name": "Qwen2.5-3B-Instruct",
            "model_size": "~2.1GB",
            "quantization": "Q4_K_M",
            "description": "A 3B parameter instruction-tuned language model optimized for local inference",
            "capabilities": [
                "Text analysis and insights",
                "Journal reflection generation",
                "Emotional tone detection",
                "Writing suggestions",
            ],
            "requirements": {
                "disk_space": "3GB (including temporary files)",
                "memory": "2GB+ RAM recommended",
                "python_version": "3.11+",
            },
        }

        if self.is_model_available():
            try:
                file_size = self.model_path.stat().st_size
                info["actual_size"] = f"{file_size / (1024**3):.1f}GB"
                info["file_path"] = str(self.model_path)
                info["status"] = "available"
            except Exception:
                info["status"] = "error"
        else:
            info["status"] = "not_downloaded"

        return info
    
    def diagnose_download_performance(self) -> Dict[str, Any]:
        """Diagnose potential download performance issues."""
        diagnosis = {
            "network_test": {},
            "disk_performance": {},
            "system_resources": {},
            "recommendations": []
        }
        
        try:
            # Test network connectivity and latency
            import socket
            import urllib.parse
            
            # Parse HuggingFace URL
            test_url = f"https://huggingface.co/{self.MODEL_REPO}/resolve/main/{self.MODEL_FILENAME}"
            parsed = urllib.parse.urlparse(test_url)
            
            # Test DNS resolution
            start_time = time.time()
            socket.gethostbyname(parsed.hostname)
            dns_time = time.time() - start_time
            diagnosis["network_test"]["dns_resolution_ms"] = round(dns_time * 1000, 2)
            
            if dns_time > 1.0:
                diagnosis["recommendations"].append("Slow DNS resolution detected - consider using different DNS servers")
            
            # Test HTTP HEAD request for latency
            start_time = time.time()
            head_response = requests.head(test_url, timeout=10)
            http_latency = time.time() - start_time
            diagnosis["network_test"]["http_latency_ms"] = round(http_latency * 1000, 2)
            diagnosis["network_test"]["server_supports_range"] = "accept-ranges" in head_response.headers
            
            if http_latency > 5.0:
                diagnosis["recommendations"].append("High network latency detected - download may be slow")
            
        except Exception as e:
            diagnosis["network_test"]["error"] = str(e)
            diagnosis["recommendations"].append("Network connectivity issues detected")
        
        try:
            # Test disk write performance
            test_file = self.models_dir / "write_test.tmp"
            test_data = b"0" * (1024 * 1024)  # 1MB test data
            
            start_time = time.time()
            with open(test_file, "wb") as f:
                for _ in range(10):  # Write 10MB
                    f.write(test_data)
                f.flush()
                os.fsync(f.fileno())
            write_time = time.time() - start_time
            
            # Clean up test file
            test_file.unlink()
            
            write_speed_mbps = 10 / write_time  # 10MB / time taken
            diagnosis["disk_performance"]["write_speed_mbps"] = round(write_speed_mbps, 2)
            
            if write_speed_mbps < 10:
                diagnosis["recommendations"].append("Slow disk write speed detected - consider freeing disk space or using SSD")
                
        except Exception as e:
            diagnosis["disk_performance"]["error"] = str(e)
            diagnosis["recommendations"].append("Unable to test disk performance")
        
        try:
            # Check system resources
            memory = psutil.virtual_memory()
            disk = shutil.disk_usage(self.models_dir)
            
            diagnosis["system_resources"]["available_memory_gb"] = round(memory.available / (1024**3), 2)
            diagnosis["system_resources"]["memory_usage_percent"] = memory.percent
            diagnosis["system_resources"]["available_disk_gb"] = round(disk.free / (1024**3), 2)
            
            if memory.percent > 90:
                diagnosis["recommendations"].append("High memory usage - close other applications")
            
            if disk.free < 5 * 1024**3:  # Less than 5GB
                diagnosis["recommendations"].append("Low disk space - free up space before downloading")
                
        except Exception as e:
            diagnosis["system_resources"]["error"] = str(e)
        
        return diagnosis


# Utility functions for UI integration
def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def format_speed(bytes_per_second: float) -> str:
    """Format download speed into human-readable format."""
    return f"{format_bytes(int(bytes_per_second))}/s"


def format_eta(seconds: Optional[int]) -> str:
    """Format estimated time remaining."""
    if seconds is None:
        return "Calculating..."

    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
