"""
AI Reflection Service

Orchestrates the AI inference pipeline, combining model inference, prompt engineering,
and caching to provide journal reflection capabilities.
"""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict

from .inference import AIInferenceEngine, InferenceConfig
from .prompts import JournalPromptEngine, ReflectionPromptConfig
from .download_model import ModelDownloadManager


@dataclass
class AIServiceConfig:
    """Configuration for AI Reflection Service."""

    cache_enabled: bool = True
    cache_expiry_hours: int = 24 * 7  # Cache reflections for a week
    auto_load_model: bool = True  # Load model automatically on startup
    inference_config: Optional[InferenceConfig] = None
    prompt_config: Optional[ReflectionPromptConfig] = None


@dataclass
class ReflectionResult:
    """Result from AI reflection generation."""

    insights: List[str]
    questions: List[str]
    themes: List[str]
    generated_at: str
    generation_time: float
    model_used: str
    cached: bool = False
    error: Optional[str] = None


class AIReflectionService:
    """Service for generating AI-powered journal reflections."""

    def __init__(self, config: Optional[AIServiceConfig] = None):
        self.config = config or AIServiceConfig()

        # Initialize components
        self.model_manager = ModelDownloadManager()
        self.inference_engine: Optional[AIInferenceEngine] = None
        self.prompt_engine = JournalPromptEngine(self.config.prompt_config)

        # Cache setup
        self.cache_dir = Path.home() / ".dana_journal" / "ai_cache"
        if self.config.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # State tracking
        self._service_ready = False
        self._initialization_error: Optional[str] = None
        
        # Diagnostic file for packaged apps
        self._diagnostic_file = self.cache_dir.parent / "ai_diagnostics.json"

        # Initialize inference engine if model exists (with enhanced retry for packaged apps)
        if self.model_manager.is_model_available():
            self._initialize_inference_engine()
        elif self._should_retry_model_check():
            # Enhanced retry logic for packaged app environments
            self._retry_model_initialization()

    def _should_retry_model_check(self) -> bool:
        """Check if we should retry model validation with enhanced logic for packaged apps."""
        # Enhanced retry conditions for packaged environments
        try:
            from config import app_config
            config_says_downloaded = app_config.is_ai_model_downloaded()
            file_exists = self.model_manager.model_path.exists()
            
            # Log for debugging in packaged environments
            # Write diagnostic info for packaged app debugging
            self.write_diagnostic_info({
                'event': 'retry_check',
                'config_downloaded': config_says_downloaded,
                'file_exists': file_exists,
                'model_path': str(self.model_manager.model_path)
            })
            
            return config_says_downloaded and file_exists
        except ImportError:
            # If we can't import config, check file existence with retry
            for attempt in range(3):
                if self.model_manager.model_path.exists():
                    return True
                import time
                time.sleep(0.1 * (attempt + 1))
            return False
    
    def _retry_model_initialization(self, max_retries: int = 5) -> None:
        """Enhanced model initialization retry logic for packaged apps."""
        for attempt in range(max_retries):
            try:
                # Write diagnostic info for each retry attempt
                self.write_diagnostic_info({
                    'event': 'initialization_retry',
                    'attempt': attempt + 1,
                    'max_retries': max_retries
                })
                
                # Progressive delay with longer waits for packaged apps
                if attempt > 0:
                    import time
                    delay = 0.2 * (attempt + 1)  # Increase delay each attempt
                    time.sleep(delay)
                
                # Enhanced model availability check
                if self.model_manager.is_model_available(retry_count=3):
                    if self._initialize_inference_engine():
                        self.write_diagnostic_info({
                        'event': 'initialization_success',
                        'attempt': attempt + 1
                    })
                        return
                    else:
                        self.write_diagnostic_info({
                            'event': 'initialization_failed_despite_model_available',
                            'attempt': attempt + 1,
                            'error': self._initialization_error
                        })
                else:
                    self.write_diagnostic_info({
                        'event': 'model_not_available',
                        'attempt': attempt + 1
                    })
                    
            except Exception as e:
                self.write_diagnostic_info({
                    'event': 'initialization_retry_error',
                    'attempt': attempt + 1,
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                if attempt == max_retries - 1:
                    self._initialization_error = f"Failed after {max_retries} attempts: {str(e)}"

    def _initialize_inference_engine(self) -> bool:
        """Initialize the inference engine with enhanced reliability for packaged apps."""
        try:
            model_path = self.model_manager.model_path
            
            # Validate model path before creating inference engine
            validation_result = self.model_manager.validate_model_path_for_packaged_app()
            if not validation_result["validation_successful"]:
                self._initialization_error = f"Model validation failed: {validation_result['error_message']}"
                print(f"Model validation details: {validation_result}")
                return False
            
            # Create inference config optimized for packaged apps
            inference_config = self.config.inference_config or InferenceConfig()
            # Reduce thread count for packaged apps to avoid resource conflicts
            if inference_config.n_threads > 2:
                inference_config.n_threads = 2
            
            self.inference_engine = AIInferenceEngine(model_path, inference_config)

            # Auto-load model if configured with enhanced retry
            if self.config.auto_load_model:
                success = self.inference_engine.load_model(retry_count=5)  # More retries for packaged apps
                if not success:
                    self._initialization_error = self.inference_engine._load_error
                    # Run diagnostics to help debug issues
                    diagnosis = self.inference_engine.diagnose_model_issues()
                    print(f"Model loading failed - Diagnosis: {diagnosis}")
                    return False
                else:
                    print("Model loaded successfully in inference engine")

            self._service_ready = True
            return True

        except Exception as e:
            self._initialization_error = (
                f"Failed to initialize inference engine: {str(e)}"
            )
            print(f"Inference engine initialization error: {e}")
            return False

    @property
    def is_available(self) -> bool:
        """Check if AI service is available and ready."""
        return (
            self.inference_engine is not None
            and self.inference_engine.is_available
            and self.model_manager.is_model_available()
        )

    @property
    def is_model_loaded(self) -> bool:
        """Check if the AI model is currently loaded in memory."""
        return (
            self.inference_engine is not None and self.inference_engine.is_model_loaded
        )

    @property
    def is_loading(self) -> bool:
        """Check if the AI model is currently being loaded."""
        return self.inference_engine is not None and self.inference_engine.is_loading

    @property
    def status(self) -> Dict[str, Any]:
        """Get detailed service status."""
        model_info = {}
        if self.inference_engine:
            model_info = self.inference_engine.get_model_info()

        return {
            "service_ready": self._service_ready,
            "is_available": self.is_available,
            "model_downloaded": self.model_manager.is_model_available(),
            "model_loaded": self.is_model_loaded,
            "is_loading": self.is_loading,
            "initialization_error": self._initialization_error,
            "model_info": model_info,
            "cache_enabled": self.config.cache_enabled,
            "cache_dir": str(self.cache_dir),
            "model_path": str(self.model_manager.model_path),
            "model_exists": self.model_manager.model_path.exists(),
        }

    def ensure_model_loaded(self) -> bool:
        """Ensure the AI model is loaded and ready for inference with enhanced reliability."""
        if not self.is_available:
            # Try to reinitialize if service is not available
            if self.model_manager.is_model_available():
                print("Service not available but model exists - attempting reinitialization")
                if self._initialize_inference_engine():
                    print("Reinitialization successful")
                else:
                    print("Reinitialization failed")
                    return False
            else:
                return False

        if not self.is_model_loaded:
            print("Model not loaded - attempting to load with retries")
            success = self.inference_engine.load_model(retry_count=5)
            if success:
                print("Model loaded successfully")
            else:
                print(f"Model loading failed: {self.inference_engine._load_error}")
            return success

        # Validate model health
        if not self.inference_engine.validate_model_health():
            print("Model health check failed - attempting reload")
            return self.inference_engine.load_model(retry_count=3)

        return True

    def retry_initialization(self) -> bool:
        """Manually retry AI service initialization if it failed initially."""
        if not self.is_available and self.model_manager.is_model_available():
            return self._initialize_inference_engine()
        return self.is_available

    async def generate_reflection(
        self,
        content: str,
        entry_date: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        force_regenerate: bool = False,
    ) -> ReflectionResult:
        """
        Generate AI reflection for journal content.

        Args:
            content: Journal entry content
            entry_date: Optional entry date for context
            progress_callback: Optional callback for progress updates
            force_regenerate: Skip cache and force new generation

        Returns:
            ReflectionResult: Generated reflection or error information
        """
        start_time = time.time()

        # Validate content
        if not self.prompt_engine.validate_content_for_reflection(content):
            return ReflectionResult(
                insights=[
                    "This entry is quite brief. Consider adding more thoughts for AI analysis."
                ],
                questions=["What else would you like to explore about this topic?"],
                themes=["reflection"],
                generated_at=datetime.now().isoformat(),
                generation_time=time.time() - start_time,
                model_used="none",
                error="Content too brief for meaningful reflection",
            )

        # Check cache first (if enabled and not forcing regeneration)
        if self.config.cache_enabled and not force_regenerate:
            cached_result = self._get_cached_reflection(content, entry_date)
            if cached_result:
                cached_result.cached = True
                cached_result.generation_time = time.time() - start_time  # Update with cache retrieval time
                return cached_result

        # Ensure AI service is ready
        if not self.is_available:
            return ReflectionResult(
                insights=["AI reflection is not currently available."],
                questions=["What insights can you draw from this entry on your own?"],
                themes=["reflection"],
                generated_at=datetime.now().isoformat(),
                generation_time=time.time() - start_time,
                model_used="none",
                error="AI service not available",
            )

        # Wait for model to load if it's currently loading
        if self.is_loading:
            if progress_callback:
                progress_callback("Loading AI model...")

            # Wait for model loading to complete
            import time as time_module

            max_wait_time = 60  # Maximum 60 seconds wait
            wait_start = time_module.time()

            while self.is_loading and (time_module.time() - wait_start) < max_wait_time:
                time_module.sleep(1)
                if progress_callback:
                    progress_callback("Loading AI model...")

            # If still loading after timeout, show error
            if self.is_loading:
                return ReflectionResult(
                    insights=["AI model is taking longer than expected to load."],
                    questions=["What thoughts come to mind when you read this entry?"],
                    themes=["reflection"],
                    generated_at=datetime.now().isoformat(),
                    generation_time=time.time() - start_time,
                    model_used="none",
                    error="Model loading timeout",
                )

        # Load model if needed
        if not self.ensure_model_loaded():
            return ReflectionResult(
                insights=["Unable to load AI model at this time."],
                questions=["What thoughts come to mind when you read this entry?"],
                themes=["reflection"],
                generated_at=datetime.now().isoformat(),
                generation_time=time.time() - start_time,
                model_used="none",
                error="Failed to load AI model",
            )

        try:
            # Generate prompt
            prompt = self.prompt_engine.create_reflection_prompt(content, entry_date)
            if not prompt:
                return ReflectionResult(
                    insights=["This entry is too brief for AI analysis."],
                    questions=["What more could you add to this reflection?"],
                    themes=["reflection"],
                    generated_at=datetime.now().isoformat(),
                    generation_time=time.time() - start_time,
                    model_used="none",
                    error="Content insufficient for prompt generation",
                )

            # Update progress
            if progress_callback:
                progress_callback("Generating AI reflection...")

            # Generate response
            inference_result = await self.inference_engine.generate_text_async(
                prompt=prompt,
                progress_callback=lambda text: (
                    progress_callback(f"Processing AI response... ({len(text)} chars)")
                    if progress_callback
                    else None
                ),
            )

            # Check for inference errors
            if "error" in inference_result:
                return ReflectionResult(
                    insights=["AI analysis encountered an issue."],
                    questions=["What can you reflect on from this entry yourself?"],
                    themes=["reflection"],
                    generated_at=datetime.now().isoformat(),
                    generation_time=time.time() - start_time,
                    model_used="qwen2.5-3b",
                    error=inference_result["error"],
                )

            # Parse response
            raw_text = inference_result.get("text", "")
            parsed_response = self.prompt_engine.parse_reflection_response(raw_text)

            if not parsed_response.get("success", False):
                return ReflectionResult(
                    insights=["AI had difficulty analyzing this entry."],
                    questions=["What stood out to you most in this reflection?"],
                    themes=["reflection"],
                    generated_at=datetime.now().isoformat(),
                    generation_time=time.time() - start_time,
                    model_used="qwen2.5-3b",
                    error=parsed_response.get("error", "Response parsing failed"),
                )

            reflection_data = parsed_response["data"]

            # Create result
            result = ReflectionResult(
                insights=reflection_data.get("insights", []),
                questions=reflection_data.get("questions", []),
                themes=reflection_data.get("themes", []),
                generated_at=datetime.now().isoformat(),
                generation_time=time.time() - start_time,
                model_used="qwen2.5-3b",
            )

            # Cache result
            if self.config.cache_enabled:
                self._cache_reflection(content, entry_date, result)

            return result

        except Exception as e:
            return ReflectionResult(
                insights=["An error occurred during AI analysis."],
                questions=["What insights can you generate about this entry yourself?"],
                themes=["reflection"],
                generated_at=datetime.now().isoformat(),
                generation_time=time.time() - start_time,
                model_used="qwen2.5-3b",
                error=f"Generation failed: {str(e)}",
            )

    def _get_cache_key(self, content: str, entry_date: Optional[str] = None) -> str:
        """Generate cache key for content and date."""
        cache_input = f"{content}|{entry_date or ''}"
        return hashlib.sha256(cache_input.encode()).hexdigest()

    def _get_cached_reflection(
        self, content: str, entry_date: Optional[str] = None
    ) -> Optional[ReflectionResult]:
        """Get cached reflection if available and not expired."""
        if not self.config.cache_enabled:
            return None

        cache_key = self._get_cache_key(content, entry_date)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            # Check expiry
            cached_time = datetime.fromisoformat(cached_data["generated_at"])
            now = datetime.now()
            hours_elapsed = (now - cached_time).total_seconds() / 3600

            if hours_elapsed > self.config.cache_expiry_hours:
                # Remove expired cache
                cache_file.unlink(missing_ok=True)
                return None

            return ReflectionResult(**cached_data)

        except Exception:
            # Remove corrupted cache
            cache_file.unlink(missing_ok=True)
            return None

    def _cache_reflection(
        self, content: str, entry_date: Optional[str], result: ReflectionResult
    ) -> None:
        """Cache reflection result."""
        if not self.config.cache_enabled:
            return

        try:
            cache_key = self._get_cache_key(content, entry_date)
            cache_file = self.cache_dir / f"{cache_key}.json"

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False)

        except Exception:
            # Silently fail cache writes
            pass

    def clear_cache(self) -> bool:
        """Clear all cached reflections."""
        if not self.config.cache_enabled or not self.cache_dir.exists():
            return True

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            return True
        except Exception:
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.config.cache_enabled or not self.cache_dir.exists():
            return {"enabled": False}

        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "enabled": True,
            "cached_reflections": len(cache_files),
            "cache_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }

    def diagnose_and_repair(self) -> Dict[str, Any]:
        """Enhanced diagnosis and repair for AI service issues in packaged apps."""
        diagnosis = {
            "issues_found": [],
            "repairs_attempted": [],
            "repair_success": True,
            "final_status": "unknown",
            "model_validation": {},
            "inference_diagnosis": {}
        }

        print("Starting AI service diagnosis...")

        # Enhanced model file validation
        model_validation = self.model_manager.validate_model_path_for_packaged_app()
        diagnosis["model_validation"] = model_validation
        
        if not model_validation["validation_successful"]:
            diagnosis["issues_found"].append(f"Model validation failed: {model_validation['error_message']}")
            # In future, could attempt to re-download here
        
        # Enhanced inference engine diagnosis
        if self.inference_engine:
            inference_diagnosis = self.inference_engine.diagnose_model_issues()
            diagnosis["inference_diagnosis"] = inference_diagnosis
            diagnosis["issues_found"].extend(inference_diagnosis["issues_found"])
        
        # Check if inference engine needs reinitialization
        if not self.is_available and model_validation["validation_successful"]:
            diagnosis["issues_found"].append("Model available but inference engine not ready")
            diagnosis["repairs_attempted"].append("Attempting to reinitialize inference engine")
            try:
                if self._initialize_inference_engine():
                    diagnosis["repairs_attempted"].append("✅ Inference engine reinitialized successfully")
                else:
                    diagnosis["repairs_attempted"].append("❌ Failed to reinitialize inference engine")
                    diagnosis["repair_success"] = False
            except Exception as e:
                diagnosis["repairs_attempted"].append(f"❌ Error during reinitialization: {str(e)}")
                diagnosis["repair_success"] = False

        # Test model loading if engine is available
        if self.is_available and not self.is_model_loaded:
            diagnosis["issues_found"].append("Inference engine available but model not loaded")
            diagnosis["repairs_attempted"].append("Attempting to load model")
            try:
                if self.ensure_model_loaded():
                    diagnosis["repairs_attempted"].append("✅ Model loaded successfully")
                else:
                    diagnosis["repairs_attempted"].append("❌ Failed to load model")
                    diagnosis["repair_success"] = False
            except Exception as e:
                diagnosis["repairs_attempted"].append(f"❌ Error loading model: {str(e)}")
                diagnosis["repair_success"] = False

        # Check cache directory
        if self.config.cache_enabled and not self.cache_dir.exists():
            diagnosis["issues_found"].append("Cache directory missing")
            diagnosis["repairs_attempted"].append("Attempting to recreate cache directory")
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                diagnosis["repairs_attempted"].append("✅ Cache directory recreated")
            except Exception as e:
                diagnosis["repairs_attempted"].append(f"❌ Failed to create cache directory: {str(e)}")
                diagnosis["repair_success"] = False

        # Final status check
        diagnosis["final_status"] = "available" if self.is_available else "unavailable"
        
        print(f"Diagnosis complete. Final status: {diagnosis['final_status']}")
        if diagnosis["issues_found"]:
            print(f"Issues found: {len(diagnosis['issues_found'])}")
        if diagnosis["repairs_attempted"]:
            print(f"Repairs attempted: {len(diagnosis['repairs_attempted'])}")
        
        return diagnosis
    
    def write_diagnostic_info(self, info: Dict[str, Any]) -> None:
        """Write diagnostic information to file for packaged app debugging."""
        try:
            # Ensure parent directory exists
            self._diagnostic_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing diagnostics or create new
            diagnostics = []
            if self._diagnostic_file.exists():
                try:
                    with open(self._diagnostic_file, 'r', encoding='utf-8') as f:
                        diagnostics = json.load(f)
                except (json.JSONDecodeError, IOError):
                    diagnostics = []
            
            # Add new diagnostic entry with timestamp
            diagnostics.append({
                'timestamp': datetime.now().isoformat(),
                'info': info
            })
            
            # Keep only last 50 entries to prevent file from growing too large
            diagnostics = diagnostics[-50:]
            
            # Write back to file
            with open(self._diagnostic_file, 'w', encoding='utf-8') as f:
                json.dump(diagnostics, f, indent=2, ensure_ascii=False)
                
        except Exception:
            # Silently fail diagnostic writes to avoid interfering with main functionality
            pass

    def unload_model(self) -> None:
        """Unload AI model to free memory."""
        if self.inference_engine:
            self.inference_engine.unload_model()

    def __del__(self):
        """Cleanup when service is destroyed."""
        if hasattr(self, "inference_engine") and self.inference_engine:
            self.inference_engine.unload_model()
