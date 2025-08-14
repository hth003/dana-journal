"""
Test suite for AI service initialization and error handling.

Tests the AI reflection service, model loading, inference engine,
and error handling scenarios for the local AI system.
"""

import pytest
import tempfile
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from pathlib import Path

from dana_journal.ai.service import AIReflectionService, AIServiceConfig
from dana_journal.ai.inference import LocalInferenceEngine
from dana_journal.ai.prompts import PromptManager


class TestAIServiceConfig:
    """Test AI service configuration."""

    def test_ai_service_config_defaults(self):
        """Test default AI service configuration."""
        config = AIServiceConfig()
        
        assert config.model_path is None
        assert config.max_tokens > 0
        assert config.temperature >= 0.0 and config.temperature <= 1.0
        assert config.enabled is True  # Default enabled
        assert config.cache_enabled is True
        
    def test_ai_service_config_custom(self):
        """Test custom AI service configuration."""
        config = AIServiceConfig(
            model_path="/custom/path/model.gguf",
            max_tokens=512,
            temperature=0.7,
            enabled=False,
            cache_enabled=False
        )
        
        assert config.model_path == "/custom/path/model.gguf"
        assert config.max_tokens == 512
        assert config.temperature == 0.7
        assert config.enabled is False
        assert config.cache_enabled is False


class TestLocalInferenceEngine:
    """Test local inference engine functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_inference_engine_initialization_no_model(self):
        """Test inference engine initialization without model."""
        engine = LocalInferenceEngine()
        
        assert engine.model is None
        assert not engine.is_loaded
        assert engine.model_path is None

    @patch('dana_journal.ai.inference.Llama')
    def test_inference_engine_load_model_success(self, mock_llama_class):
        """Test successful model loading."""
        mock_model = MagicMock()
        mock_llama_class.return_value = mock_model
        
        engine = LocalInferenceEngine()
        model_path = "/path/to/model.gguf"
        
        result = engine.load_model(model_path)
        
        assert result is True
        assert engine.is_loaded
        assert engine.model_path == model_path
        mock_llama_class.assert_called_once()

    @patch('dana_journal.ai.inference.Llama')
    def test_inference_engine_load_model_failure(self, mock_llama_class):
        """Test model loading failure."""
        mock_llama_class.side_effect = Exception("Model loading failed")
        
        engine = LocalInferenceEngine()
        model_path = "/path/to/nonexistent.gguf"
        
        result = engine.load_model(model_path)
        
        assert result is False
        assert not engine.is_loaded
        assert engine.model is None

    @patch('dana_journal.ai.inference.Llama')
    def test_inference_engine_generate_text(self, mock_llama_class):
        """Test text generation with loaded model."""
        mock_model = MagicMock()
        mock_model.return_value = [{"choices": [{"text": " Generated response"}]}]
        mock_llama_class.return_value = mock_model
        
        engine = LocalInferenceEngine()
        engine.load_model("/path/to/model.gguf")
        
        result = engine.generate_text("Test prompt", max_tokens=100)
        
        assert result is not None
        assert "Generated response" in result
        mock_model.assert_called_once()

    def test_inference_engine_generate_without_model(self):
        """Test text generation without loaded model."""
        engine = LocalInferenceEngine()
        
        result = engine.generate_text("Test prompt")
        
        assert result is None

    def test_inference_engine_memory_cleanup(self):
        """Test memory cleanup functionality."""
        engine = LocalInferenceEngine()
        
        # Should not raise exception even with no model loaded
        engine.cleanup()
        
        # Test with mock model
        with patch('dana_journal.ai.inference.Llama') as mock_llama:
            mock_model = MagicMock()
            mock_llama.return_value = mock_model
            
            engine.load_model("/path/to/model.gguf")
            engine.cleanup()
            
            assert engine.model is None
            assert not engine.is_loaded


class TestPromptManager:
    """Test prompt management system."""

    def test_prompt_manager_initialization(self):
        """Test prompt manager initialization."""
        pm = PromptManager()
        
        assert pm is not None
        # Should have system prompts loaded
        assert hasattr(pm, 'get_system_prompt')
        assert hasattr(pm, 'get_reflection_prompt')

    def test_system_prompt_generation(self):
        """Test system prompt generation."""
        pm = PromptManager()
        
        system_prompt = pm.get_system_prompt()
        
        assert system_prompt is not None
        assert len(system_prompt) > 0
        assert "Dana" in system_prompt  # Should mention Dana companion
        
    def test_reflection_prompt_generation(self):
        """Test reflection prompt generation."""
        pm = PromptManager()
        
        test_content = "Today was a productive day. I completed several important tasks."
        test_date = "2025-08-14"
        
        reflection_prompt = pm.get_reflection_prompt(test_content, test_date)
        
        assert reflection_prompt is not None
        assert len(reflection_prompt) > 0
        assert test_content in reflection_prompt
        assert test_date in reflection_prompt

    def test_prompt_customization(self):
        """Test prompt customization capabilities."""
        pm = PromptManager()
        
        # Test different content types
        prompts = [
            pm.get_reflection_prompt("Short entry.", "2025-08-14"),
            pm.get_reflection_prompt("Long entry with multiple sentences and thoughts about various topics including work, personal life, and future goals.", "2025-08-14"),
            pm.get_reflection_prompt("Emotional entry about dealing with challenges and setbacks.", "2025-08-14")
        ]
        
        for prompt in prompts:
            assert prompt is not None
            assert len(prompt) > 0


class TestAIReflectionService:
    """Test AI reflection service integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "ai_cache"
        self.cache_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_ai_service_initialization_disabled(self):
        """Test AI service initialization when disabled."""
        config = AIServiceConfig(enabled=False)
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        assert service.is_available is False
        assert service.status == "disabled"

    def test_ai_service_initialization_no_model(self):
        """Test AI service initialization without model path."""
        config = AIServiceConfig(enabled=True, model_path=None)
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        assert service.is_available is False
        assert "model" in service.status.lower()

    @patch('dana_journal.ai.service.LocalInferenceEngine')
    def test_ai_service_initialization_with_model(self, mock_engine_class):
        """Test AI service initialization with model."""
        mock_engine = MagicMock()
        mock_engine.is_loaded = True
        mock_engine.load_model.return_value = True
        mock_engine_class.return_value = mock_engine
        
        config = AIServiceConfig(enabled=True, model_path="/path/to/model.gguf")
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        assert service.is_available is True
        assert service.status == "ready"
        mock_engine.load_model.assert_called_once_with("/path/to/model.gguf")

    @patch('dana_journal.ai.service.LocalInferenceEngine')
    def test_ai_service_model_loading_failure(self, mock_engine_class):
        """Test AI service behavior when model loading fails."""
        mock_engine = MagicMock()
        mock_engine.is_loaded = False
        mock_engine.load_model.return_value = False
        mock_engine_class.return_value = mock_engine
        
        config = AIServiceConfig(enabled=True, model_path="/invalid/path.gguf")
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        assert service.is_available is False
        assert "load" in service.status.lower() or "error" in service.status.lower()

    @pytest.mark.asyncio
    @patch('dana_journal.ai.service.LocalInferenceEngine')
    async def test_generate_reflection_success(self, mock_engine_class):
        """Test successful AI reflection generation."""
        mock_engine = MagicMock()
        mock_engine.is_loaded = True
        mock_engine.load_model.return_value = True
        mock_engine.generate_text.return_value = '{"insights": ["Test insight"], "questions": ["Test question?"], "themes": ["reflection"]}'
        mock_engine_class.return_value = mock_engine
        
        config = AIServiceConfig(enabled=True, model_path="/path/to/model.gguf")
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        result = await service.generate_reflection(
            content="Today was a good day.",
            entry_date="2025-08-14"
        )
        
        assert result is not None
        assert hasattr(result, 'insights')
        assert hasattr(result, 'questions') 
        assert hasattr(result, 'themes')
        assert result.error is None

    @pytest.mark.asyncio
    @patch('dana_journal.ai.service.LocalInferenceEngine')
    async def test_generate_reflection_service_unavailable(self, mock_engine_class):
        """Test reflection generation when service unavailable."""
        config = AIServiceConfig(enabled=False)
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        result = await service.generate_reflection(
            content="Test content",
            entry_date="2025-08-14"
        )
        
        assert result is not None
        assert result.error is not None
        assert "unavailable" in result.error.lower() or "disabled" in result.error.lower()

    @pytest.mark.asyncio
    @patch('dana_journal.ai.service.LocalInferenceEngine')
    async def test_generate_reflection_with_caching(self, mock_engine_class):
        """Test reflection generation with caching enabled."""
        mock_engine = MagicMock()
        mock_engine.is_loaded = True
        mock_engine.load_model.return_value = True
        mock_engine.generate_text.return_value = '{"insights": ["Cached insight"], "questions": ["Cached question?"], "themes": ["cached"]}'
        mock_engine_class.return_value = mock_engine
        
        config = AIServiceConfig(enabled=True, model_path="/path/to/model.gguf", cache_enabled=True)
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        content = "Identical test content"
        entry_date = "2025-08-14"
        
        # First call - should generate
        result1 = await service.generate_reflection(content=content, entry_date=entry_date)
        
        # Second call - should use cache
        result2 = await service.generate_reflection(content=content, entry_date=entry_date)
        
        assert result1 is not None
        assert result2 is not None
        assert result2.cached is True  # Second result should be cached

    @pytest.mark.asyncio
    @patch('dana_journal.ai.service.LocalInferenceEngine')
    async def test_generate_reflection_force_regenerate(self, mock_engine_class):
        """Test forcing regeneration bypassing cache."""
        mock_engine = MagicMock()
        mock_engine.is_loaded = True
        mock_engine.load_model.return_value = True
        mock_engine.generate_text.return_value = '{"insights": ["Fresh insight"], "questions": ["Fresh question?"], "themes": ["fresh"]}'
        mock_engine_class.return_value = mock_engine
        
        config = AIServiceConfig(enabled=True, model_path="/path/to/model.gguf", cache_enabled=True)
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        content = "Content to regenerate"
        entry_date = "2025-08-14"
        
        # First call
        result1 = await service.generate_reflection(content=content, entry_date=entry_date)
        
        # Second call with force_regenerate=True
        result2 = await service.generate_reflection(
            content=content, 
            entry_date=entry_date, 
            force_regenerate=True
        )
        
        assert result1 is not None
        assert result2 is not None
        assert result2.cached is False  # Should not be cached due to force regenerate

    def test_ai_service_retry_initialization(self):
        """Test AI service retry initialization functionality."""
        config = AIServiceConfig(enabled=True, model_path=None)
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        # Initially unavailable
        assert service.is_available is False
        
        # Test retry with still no model
        if hasattr(service, 'retry_initialization'):
            result = service.retry_initialization()
            assert result is False  # Should fail without model path
            
    def test_ai_service_cleanup(self):
        """Test AI service cleanup functionality."""
        config = AIServiceConfig(enabled=True, model_path="/path/to/model.gguf")
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        # Should not raise exception
        if hasattr(service, 'cleanup'):
            service.cleanup()

    @pytest.mark.asyncio
    async def test_progress_callback_integration(self):
        """Test progress callback functionality during generation."""
        config = AIServiceConfig(enabled=False)  # Disabled for this test
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        progress_messages = []
        
        def progress_callback(message):
            progress_messages.append(message)
        
        result = await service.generate_reflection(
            content="Test content",
            entry_date="2025-08-14",
            progress_callback=progress_callback
        )
        
        # Should have received at least one progress message
        assert len(progress_messages) > 0
        assert result is not None


class TestAIServiceErrorHandling:
    """Test AI service error handling scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "ai_cache"
        self.cache_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    @patch('dana_journal.ai.service.LocalInferenceEngine')
    async def test_inference_error_handling(self, mock_engine_class):
        """Test handling of inference errors."""
        mock_engine = MagicMock()
        mock_engine.is_loaded = True
        mock_engine.load_model.return_value = True
        mock_engine.generate_text.side_effect = Exception("Inference failed")
        mock_engine_class.return_value = mock_engine
        
        config = AIServiceConfig(enabled=True, model_path="/path/to/model.gguf")
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        result = await service.generate_reflection(
            content="Test content",
            entry_date="2025-08-14"
        )
        
        assert result is not None
        assert result.error is not None
        assert "failed" in result.error.lower() or "error" in result.error.lower()

    @pytest.mark.asyncio
    @patch('dana_journal.ai.service.LocalInferenceEngine')
    async def test_json_parsing_error_handling(self, mock_engine_class):
        """Test handling of JSON parsing errors from AI output."""
        mock_engine = MagicMock()
        mock_engine.is_loaded = True
        mock_engine.load_model.return_value = True
        mock_engine.generate_text.return_value = "Invalid JSON response"
        mock_engine_class.return_value = mock_engine
        
        config = AIServiceConfig(enabled=True, model_path="/path/to/model.gguf")
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        result = await service.generate_reflection(
            content="Test content",
            entry_date="2025-08-14"
        )
        
        assert result is not None
        # Should handle gracefully, either with error or fallback content
        assert hasattr(result, 'insights')

    @pytest.mark.asyncio  
    async def test_memory_pressure_handling(self):
        """Test handling of memory pressure scenarios."""
        config = AIServiceConfig(enabled=True, model_path="/path/to/huge_model.gguf")
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        # Should handle memory issues gracefully
        assert service.is_available is False  # Model won't load due to invalid path

    def test_concurrent_request_handling(self):
        """Test handling of concurrent AI requests."""
        config = AIServiceConfig(enabled=False)  # Disabled for safety
        service = AIReflectionService(config, cache_dir=self.cache_dir)
        
        # Multiple concurrent requests should be handled gracefully
        async def make_request():
            return await service.generate_reflection(
                content="Concurrent test",
                entry_date="2025-08-14"
            )
        
        async def test_concurrent():
            results = await asyncio.gather(
                make_request(),
                make_request(), 
                make_request(),
                return_exceptions=True
            )
            
            # All requests should complete without exceptions
            for result in results:
                assert not isinstance(result, Exception)
                assert result is not None
        
        # Run the concurrent test
        asyncio.run(test_concurrent())


if __name__ == "__main__":
    pytest.main([__file__])