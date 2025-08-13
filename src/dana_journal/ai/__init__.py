"""AI integration and reflection generation."""

from .download_model import (
    ModelDownloadManager,
    DownloadProgress,
    format_bytes,
    format_speed,
    format_eta,
)
from .inference import AIInferenceEngine, InferenceConfig
from .prompts import JournalPromptEngine, ReflectionPromptConfig
from .service import AIReflectionService, AIServiceConfig, ReflectionResult

__all__ = [
    # Model downloading
    "ModelDownloadManager",
    "DownloadProgress",
    "format_bytes",
    "format_speed",
    "format_eta",
    # AI inference
    "AIInferenceEngine",
    "InferenceConfig",
    # Prompt engineering
    "JournalPromptEngine",
    "ReflectionPromptConfig",
    # AI service
    "AIReflectionService",
    "AIServiceConfig",
    "ReflectionResult",
]
