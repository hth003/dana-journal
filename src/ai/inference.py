"""
AI Inference Engine

Handles local AI inference using llama-cpp-python for generating journal reflections.
Provides thread-safe, async-compatible inference with memory management.
"""

import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

try:
    from llama_cpp import Llama

    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class InferenceConfig:
    """Configuration for AI inference."""

    n_threads: int = 4  # Number of CPU threads to use
    n_ctx: int = 2048  # Context window size
    temperature: float = 0.7  # Sampling temperature
    max_tokens: int = 512  # Maximum tokens to generate
    top_p: float = 0.95  # Top-p sampling
    stop_sequences: list = None  # Stop sequences for generation

    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = ["\n\n", "```", "---"]


class AIInferenceEngine:
    """Local AI inference engine using llama-cpp-python."""

    def __init__(self, model_path: Path, config: Optional[InferenceConfig] = None):
        self.model_path = model_path
        self.config = config or InferenceConfig()
        self._model: Optional[Llama] = None
        self._lock = threading.RLock()
        self._loading = False
        self._load_error: Optional[str] = None

    @property
    def is_available(self) -> bool:
        """Check if llama-cpp-python is available."""
        return LLAMA_CPP_AVAILABLE

    @property
    def is_model_loaded(self) -> bool:
        """Check if model is currently loaded."""
        with self._lock:
            return self._model is not None

    @property
    def is_loading(self) -> bool:
        """Check if model is currently being loaded."""
        with self._lock:
            return self._loading

    def validate_model_health(self) -> bool:
        """Validate that the model is healthy and ready for inference with enhanced checks."""
        with self._lock:
            if self._model is None:
                return False

            # Check if the model object is still valid
            try:
                # Enhanced validation for packaged app environments
                if not hasattr(self._model, "__call__"):
                    self._model = None
                    return False
                
                # Additional health checks for packaged apps
                if not hasattr(self._model, "_model"):
                    self._model = None
                    return False
                
                # Try a minimal inference to test model health
                try:
                    # Simple test with minimal tokens
                    test_result = self._model("test", max_tokens=1, temperature=0.1)
                    if not isinstance(test_result, dict) or "choices" not in test_result:
                        self._model = None
                        return False
                except Exception:
                    # If test inference fails, model is unhealthy
                    self._model = None
                    return False
                
                return True
                
            except Exception:
                # If any exception occurs, consider model unhealthy
                self._model = None
                return False
    
    def diagnose_model_issues(self) -> Dict[str, Any]:
        """Comprehensive diagnosis for model loading issues in packaged apps."""
        diagnosis = {
            "model_path_exists": False,
            "model_file_readable": False,
            "model_size_valid": False,
            "llama_cpp_available": self.is_available,
            "memory_sufficient": False,
            "model_loaded": self.is_model_loaded,
            "model_healthy": False,
            "issues_found": [],
            "recommendations": []
        }
        
        try:
            # Check model path
            diagnosis["model_path_exists"] = self.model_exists
            if not diagnosis["model_path_exists"]:
                diagnosis["issues_found"].append(f"Model file not found: {self.model_path}")
                diagnosis["recommendations"].append("Download the AI model through the onboarding process")
            
            # Check file readability
            if diagnosis["model_path_exists"]:
                try:
                    with open(self.model_path, "rb") as f:
                        f.read(4)  # Try to read header
                    diagnosis["model_file_readable"] = True
                except (OSError, IOError, PermissionError) as e:
                    diagnosis["issues_found"].append(f"Model file not readable: {e}")
                    diagnosis["recommendations"].append("Check file permissions or re-download the model")
            
            # Check model size
            if diagnosis["model_file_readable"]:
                try:
                    file_size = self.model_path.stat().st_size
                    if 1_000_000_000 <= file_size <= 3_000_000_000:
                        diagnosis["model_size_valid"] = True
                    else:
                        diagnosis["issues_found"].append(f"Invalid model file size: {file_size} bytes")
                        diagnosis["recommendations"].append("Re-download the model - file may be corrupted")
                except Exception as e:
                    diagnosis["issues_found"].append(f"Cannot check model file size: {e}")
            
            # Check memory
            diagnosis["memory_sufficient"] = self.check_memory_requirements()
            if not diagnosis["memory_sufficient"]:
                memory_info = self.get_memory_usage()
                diagnosis["issues_found"].append(f"Insufficient memory: {memory_info.get('available_memory_gb', 'unknown')}GB available")
                diagnosis["recommendations"].append("Close other applications to free memory")
            
            # Check model health if loaded
            if self.is_model_loaded:
                diagnosis["model_healthy"] = self.validate_model_health()
                if not diagnosis["model_healthy"]:
                    diagnosis["issues_found"].append("Model loaded but not responding correctly")
                    diagnosis["recommendations"].append("Restart the application to reload the model")
            
        except Exception as e:
            diagnosis["issues_found"].append(f"Diagnosis error: {e}")
        
        return diagnosis

    @property
    def model_exists(self) -> bool:
        """Check if model file exists with enhanced validation for packaged apps."""
        try:
            # Basic existence check
            if not self.model_path.exists():
                return False
            
            # Verify it's actually a file and accessible
            if not self.model_path.is_file():
                return False
            
            # Try to access the file to ensure it's readable
            try:
                with open(self.model_path, "rb") as f:
                    f.read(1)  # Read one byte to test accessibility
                return True
            except (OSError, IOError, PermissionError):
                return False
                
        except Exception:
            return False

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        memory_info = {
            "available": PSUTIL_AVAILABLE,
            "system_memory_gb": 0,
            "available_memory_gb": 0,
            "memory_usage_percent": 0,
            "model_loaded": self.is_model_loaded,
        }

        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                memory_info.update(
                    {
                        "system_memory_gb": round(memory.total / (1024**3), 2),
                        "available_memory_gb": round(memory.available / (1024**3), 2),
                        "memory_usage_percent": memory.percent,
                    }
                )
            except Exception:
                pass

        return memory_info

    def check_memory_requirements(self, required_gb: float = 2.5) -> bool:
        """Check if system has enough memory for model loading."""
        if not PSUTIL_AVAILABLE:
            return True  # Can't check, assume it's okay

        try:
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            return available_gb >= required_gb
        except Exception:
            return True  # Error checking, assume it's okay

    def load_model(self, retry_count: int = 3) -> bool:
        """
        Load the AI model into memory with enhanced reliability for packaged apps.

        Args:
            retry_count: Number of retry attempts for model loading

        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        if not self.is_available:
            self._load_error = "llama-cpp-python not available. Please install it."
            return False

        # Enhanced model existence check with retries
        model_exists = False
        for attempt in range(retry_count):
            if self.model_exists:
                model_exists = True
                break
            if attempt < retry_count - 1:
                import time
                time.sleep(0.2 * (attempt + 1))  # Progressive delay
        
        if not model_exists:
            self._load_error = f"Model file not found after {retry_count} attempts: {self.model_path}"
            return False

        # Check memory requirements
        if not self.check_memory_requirements():
            memory_info = self.get_memory_usage()
            self._load_error = f"Insufficient memory. Available: {memory_info.get('available_memory_gb', 'unknown')}GB, Required: ~2.5GB"
            return False

        with self._lock:
            if self._model is not None:
                return True  # Already loaded

            if self._loading:
                return False  # Loading in progress

            self._loading = True
            self._load_error = None

        # Try loading with exponential backoff
        last_error = None
        for attempt in range(retry_count):
            try:
                # Verify file accessibility before loading
                try:
                    with open(self.model_path, "rb") as f:
                        f.read(4)  # Try to read GGUF header
                except (OSError, IOError, PermissionError) as file_error:
                    if attempt < retry_count - 1:
                        import time
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    raise file_error

                # Load model with configuration optimized for packaged apps
                self._model = Llama(
                    model_path=str(self.model_path),
                    n_threads=self.config.n_threads,
                    n_ctx=self.config.n_ctx,
                    verbose=False,  # Suppress llama.cpp logs
                    use_mlock=False,  # Disable mlock for packaged apps - can cause issues
                    use_mmap=True,  # Use memory mapping for efficiency
                    n_gpu_layers=0,  # Ensure CPU-only inference for compatibility
                )

                with self._lock:
                    self._loading = False

                return True

            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    # Exponential backoff with jitter
                    import time
                    import random
                    delay = (0.5 * (2 ** attempt)) + random.uniform(0, 0.1)
                    time.sleep(delay)
                    print(f"Model loading attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                    continue
                break

        # All attempts failed
        self._load_error = f"Failed to load model after {retry_count} attempts: {str(last_error)}"
        with self._lock:
            self._model = None
            self._loading = False
        return False

    def unload_model(self) -> None:
        """Unload the model from memory to free resources."""
        with self._lock:
            if self._model is not None:
                # llama-cpp-python handles cleanup automatically
                self._model = None

    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate text using the loaded model.

        Args:
            prompt: Input prompt for generation
            max_tokens: Maximum tokens to generate (overrides config)
            temperature: Sampling temperature (overrides config)
            progress_callback: Optional callback for streaming generation

        Returns:
            Dict containing 'text', 'tokens_generated', 'generation_time'
        """
        # Check if model is loaded (don't validate health unless there's an issue)
        if not self.is_model_loaded:
            if not self.load_model():
                return {
                    "text": "",
                    "tokens_generated": 0,
                    "generation_time": 0.0,
                    "error": self._load_error or "Model not loaded",
                }

        # Use provided values or fall back to config
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature

        start_time = time.time()

        try:
            with self._lock:
                if self._model is None:
                    return {
                        "text": "",
                        "tokens_generated": 0,
                        "generation_time": 0.0,
                        "error": "Model not available",
                    }

                # Generate text
                if progress_callback:
                    # Streaming generation
                    generated_text = ""
                    token_count = 0

                    for output in self._model(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=self.config.top_p,
                        stop=self.config.stop_sequences,
                        stream=True,
                    ):
                        if "choices" in output and len(output["choices"]) > 0:
                            chunk = output["choices"][0].get("text", "")
                            generated_text += chunk
                            token_count += 1

                            # Call progress callback
                            progress_callback(generated_text)

                            # Check for stop sequences
                            if any(
                                stop in generated_text
                                for stop in self.config.stop_sequences
                            ):
                                break

                    result_text = generated_text
                    tokens_generated = token_count
                else:
                    # Non-streaming generation
                    result = self._model(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=self.config.top_p,
                        stop=self.config.stop_sequences,
                    )

                    result_text = result["choices"][0]["text"]
                    tokens_generated = len(
                        result.get("choices", [{}])[0].get("text", "").split()
                    )

            generation_time = time.time() - start_time

            return {
                "text": result_text.strip(),
                "tokens_generated": tokens_generated,
                "generation_time": generation_time,
            }

        except Exception as e:
            generation_time = time.time() - start_time

            # If generation fails, validate model health and try recovery
            if not self.validate_model_health():
                if self.load_model():
                    # Could retry generation here, but for now just return error
                    pass

            return {
                "text": "",
                "tokens_generated": 0,
                "generation_time": generation_time,
                "error": f"Generation failed: {str(e)}",
            }

    async def generate_text_async(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Async wrapper for text generation.

        Runs inference in a thread pool to avoid blocking the UI.
        """
        loop = asyncio.get_event_loop()

        # Run in thread pool to avoid blocking
        result = await loop.run_in_executor(
            None, self.generate_text, prompt, max_tokens, temperature, progress_callback
        )

        return result

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_path": str(self.model_path),
            "model_exists": self.model_exists,
            "is_loaded": self.is_model_loaded,
            "is_loading": self._loading,
            "load_error": self._load_error,
            "config": {
                "n_threads": self.config.n_threads,
                "n_ctx": self.config.n_ctx,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
            },
        }

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.unload_model()
