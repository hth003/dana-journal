"""
AI Model Download Manager

Handles downloading and managing the Qwen2.5-3B-Instruct model for local AI insights.
Uses huggingface-hub to download GGUF models to ~/.journal_vault/models/ directory.
"""

import sys
import time
import shutil
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
        self.models_dir = Path.home() / ".journal_vault" / "models"
        self.model_path = self.models_dir / self.MODEL_FILENAME
        self.temp_path = self.models_dir / f"{self.MODEL_FILENAME}.tmp"
        self.progress = DownloadProgress()
        self.download_thread: Optional[threading.Thread] = None
        self.cancel_requested = False

        # Create models directory
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def is_model_available(self) -> bool:
        """Check if the model is already downloaded and valid."""
        if not self.model_path.exists():
            return False

        # Check file size is reasonable (at least 1GB, not more than 3GB)
        try:
            file_size = self.model_path.stat().st_size
            if file_size < 1_000_000_000 or file_size > 3_000_000_000:
                return False

            # Basic validation - try to read the first few bytes
            with open(self.model_path, "rb") as f:
                header = f.read(4)
                # GGUF files start with 'GGUF' magic bytes
                if header != b"GGUF":
                    return False

            return True
        except (OSError, IOError):
            return False

    def get_model_path(self) -> Optional[Path]:
        """Get the path to the downloaded model file."""
        if self.is_model_available():
            return self.model_path
        return None

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
        """Direct download with requests for better progress tracking."""
        # Construct download URL
        url = f"https://huggingface.co/{self.MODEL_REPO}/resolve/main/{self.MODEL_FILENAME}"

        start_time = time.time()
        last_update_time = start_time

        try:
            # Use longer timeout for large file download
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            # Get total size from headers
            total_size = int(
                response.headers.get("content-length", self.MODEL_SIZE_BYTES)
            )
            self.progress.total_bytes = total_size

            # Download with progress tracking
            with open(self.temp_path, "wb") as f:
                bytes_downloaded = 0

                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancel_requested:
                        raise InterruptedError("Download cancelled")

                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)

                        # Update progress every 0.5 seconds
                        current_time = time.time()
                        if current_time - last_update_time > 0.5:
                            self.progress.bytes_downloaded = bytes_downloaded

                            # Calculate download speed
                            time_elapsed = current_time - start_time
                            if time_elapsed > 0:
                                self.progress.download_speed = (
                                    bytes_downloaded / time_elapsed
                                )

                                # Estimate time remaining
                                remaining_bytes = total_size - bytes_downloaded
                                if self.progress.download_speed > 0:
                                    self.progress.eta_seconds = int(
                                        remaining_bytes / self.progress.download_speed
                                    )

                            progress_callback()
                            last_update_time = current_time

            # Final progress update
            self.progress.bytes_downloaded = bytes_downloaded
            progress_callback()

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
