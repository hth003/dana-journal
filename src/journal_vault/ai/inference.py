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
    def model_exists(self) -> bool:
        """Check if model file exists."""
        return self.model_path.exists() and self.model_path.is_file()

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

    def load_model(self) -> bool:
        """
        Load the AI model into memory.

        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        if not self.is_available:
            self._load_error = "llama-cpp-python not available. Please install it."
            return False

        if not self.model_exists:
            self._load_error = f"Model file not found: {self.model_path}"
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

        try:
            # Load model with configuration
            self._model = Llama(
                model_path=str(self.model_path),
                n_threads=self.config.n_threads,
                n_ctx=self.config.n_ctx,
                verbose=False,  # Suppress llama.cpp logs
                use_mlock=True,  # Lock model in memory
                use_mmap=True,  # Use memory mapping for efficiency
            )

            with self._lock:
                self._loading = False

            return True

        except Exception as e:
            self._load_error = f"Failed to load model: {str(e)}"
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
