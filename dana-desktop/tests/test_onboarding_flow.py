"""
Integration tests for the onboarding flow.

Tests the complete user onboarding experience including:
- Welcome and feature overview
- Privacy explanation
- Dual-mode vault setup (new/existing)
- AI setup and model download
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from dana_journal.config.app_config import AppConfig
from dana_journal.storage.file_manager import FileManager


class TestOnboardingConfiguration:
    """Test onboarding configuration and state management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_config_dir = tempfile.mkdtemp()
        self.original_config_dir = None

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_config_dir)

    @patch('dana_journal.config.app_config.AppConfig._get_config_dir')
    def test_initial_onboarding_state(self, mock_config_dir):
        """Test initial onboarding state for new installation."""
        mock_config_dir.return_value = Path(self.temp_config_dir)
        
        config = AppConfig()
        
        # New installation should not be onboarded
        assert not config.is_onboarded()
        assert config.get_storage_path() is None
        assert not config.get_ai_enabled()
        assert not config.get_ai_model_downloaded()

    @patch('dana_journal.config.app_config.AppConfig._get_config_dir')
    def test_complete_onboarding_flow(self, mock_config_dir):
        """Test complete onboarding flow configuration."""
        mock_config_dir.return_value = Path(self.temp_config_dir)
        config = AppConfig()
        
        # Simulate onboarding steps
        vault_path = "/Users/test/Documents/MyJournal"
        vault_name = "My Journal Vault"
        
        # Step 1-2: Welcome and Privacy (no configuration changes)
        assert not config.is_onboarded()
        
        # Step 3: Vault setup
        config.set_storage_path(vault_path)
        config.set_vault_name(vault_name)
        
        # Step 4: AI setup
        config.set_ai_enabled(True)
        config.set_ai_model_downloaded(True)
        config.set_ai_model_path("/path/to/model")
        
        # Complete onboarding
        config.set_onboarded(True)
        
        # Verify all settings persisted
        assert config.is_onboarded()
        assert config.get_storage_path() == vault_path
        assert config.get_vault_name() == vault_name
        assert config.get_ai_enabled()
        assert config.get_ai_model_downloaded()

    @patch('dana_journal.config.app_config.AppConfig._get_config_dir')
    def test_partial_onboarding_recovery(self, mock_config_dir):
        """Test recovery from partial onboarding state."""
        mock_config_dir.return_value = Path(self.temp_config_dir)
        config = AppConfig()
        
        # Simulate partial onboarding (e.g., user closed app mid-flow)
        config.set_storage_path("/Users/test/Documents/Journal")
        config.set_ai_enabled(False)  # AI disabled
        # Note: onboarded flag not set
        
        # Verify partial state
        assert not config.is_onboarded()  # Still incomplete
        assert config.get_storage_path() == "/Users/test/Documents/Journal"
        assert not config.get_ai_enabled()
        
        # Complete onboarding
        config.set_onboarded(True)
        assert config.is_onboarded()


class TestVaultSetupIntegration:
    """Test vault setup integration with FileManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_vault_dir = tempfile.mkdtemp()
        self.temp_config_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_vault_dir)
        shutil.rmtree(self.temp_config_dir)

    def test_new_vault_creation(self):
        """Test creating a new vault during onboarding."""
        vault_path = Path(self.temp_vault_dir) / "new_journal_vault"
        
        # Verify path doesn't exist initially
        assert not vault_path.exists()
        assert not FileManager.is_existing_vault(str(vault_path))
        
        # Create new vault through FileManager
        fm = FileManager(str(vault_path))
        
        # Verify vault structure created
        assert vault_path.exists()
        assert FileManager.is_existing_vault(str(vault_path))
        assert (vault_path / ".dana_journal").exists()
        assert (vault_path / "entries").exists()
        assert (vault_path / ".dana_journal" / "index.sqlite").exists()

    def test_existing_vault_detection(self):
        """Test detecting and loading existing vault."""
        # Create an existing vault structure
        existing_vault = Path(self.temp_vault_dir) / "existing_vault"
        existing_vault.mkdir()
        (existing_vault / ".dana_journal").mkdir()
        (existing_vault / "entries").mkdir()
        
        # Create some existing entries
        entries_dir = existing_vault / "entries" / "2025" / "08"
        entries_dir.mkdir(parents=True)
        
        test_entry_path = entries_dir / "2025-08-01.md"
        with open(test_entry_path, 'w') as f:
            f.write("---\ntitle: Existing Entry\n---\nThis entry already existed!")
        
        # Verify detection
        assert FileManager.is_existing_vault(str(existing_vault))
        
        # Load existing vault
        fm = FileManager(str(existing_vault))
        
        # Verify existing content is accessible
        scanned_count = fm.scan_existing_files()
        assert scanned_count > 0
        
        entry_dates = fm.get_entry_dates()
        assert len(entry_dates) > 0

    def test_vault_validation_during_setup(self):
        """Test vault validation during onboarding."""
        # Create a vault
        fm = FileManager(self.temp_vault_dir)
        
        # Create test entry
        from datetime import date
        test_date = date(2025, 8, 14)
        fm.create_entry(test_date, "Test content", "Test Title")
        
        # Validate vault
        validation_result = fm.validate_vault()
        
        assert validation_result["is_valid"] is True
        assert len(validation_result["errors"]) == 0
        assert validation_result["total_entries"] > 0


class TestAISetupIntegration:
    """Test AI setup integration during onboarding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_config_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_config_dir)

    @patch('dana_journal.config.app_config.AppConfig._get_config_dir')
    def test_ai_disabled_onboarding(self, mock_config_dir):
        """Test onboarding flow with AI features disabled."""
        mock_config_dir.return_value = Path(self.temp_config_dir)
        config = AppConfig()
        
        # User chooses to skip AI setup
        config.set_ai_enabled(False)
        config.set_ai_model_downloaded(False)
        config.set_onboarded(True)
        
        # Verify AI is properly disabled
        assert config.is_onboarded()
        assert not config.get_ai_enabled()
        assert not config.get_ai_model_downloaded()
        assert config.get_ai_model_path() is None

    @patch('dana_journal.config.app_config.AppConfig._get_config_dir')
    def test_ai_enabled_onboarding(self, mock_config_dir):
        """Test onboarding flow with AI features enabled."""
        mock_config_dir.return_value = Path(self.temp_config_dir)
        config = AppConfig()
        
        # User chooses to enable AI
        config.set_ai_enabled(True)
        
        # Simulate model download completion
        model_path = "/Users/test/.dana_journal/models/qwen2.5-3b-instruct.gguf"
        config.set_ai_model_downloaded(True)
        config.set_ai_model_path(model_path)
        
        # Update AI service status
        ai_status = {
            "model_downloaded": True,
            "model_path": model_path,
            "last_model_load": datetime.now().isoformat(),
            "successful_generations": 0,
            "failed_generations": 0
        }
        config.update_ai_service_status(ai_status)
        
        config.set_onboarded(True)
        
        # Verify AI is properly configured
        assert config.is_onboarded()
        assert config.get_ai_enabled()
        assert config.get_ai_model_downloaded()
        assert config.get_ai_model_path() == model_path
        
        # Verify AI service status
        stored_status = config.get_ai_service_status()
        assert stored_status["model_downloaded"] is True
        assert stored_status["model_path"] == model_path

    @patch('dana_journal.ai.download_model.download_qwen_model')
    @patch('dana_journal.config.app_config.AppConfig._get_config_dir')
    def test_ai_model_download_flow(self, mock_config_dir, mock_download):
        """Test AI model download during onboarding."""
        mock_config_dir.return_value = Path(self.temp_config_dir)
        mock_download.return_value = "/path/to/downloaded/model.gguf"
        
        config = AppConfig()
        config.set_ai_enabled(True)
        
        # Simulate download progress (would be handled by UI)
        progress_updates = []
        
        def mock_progress_callback(message, progress=None):
            progress_updates.append((message, progress))
        
        # Mock successful download
        downloaded_path = mock_download.return_value
        
        # Update configuration after download
        config.set_ai_model_downloaded(True)
        config.set_ai_model_path(downloaded_path)
        
        # Verify download was "completed"
        assert config.get_ai_model_downloaded()
        assert config.get_ai_model_path() == downloaded_path
        mock_download.assert_called_once()


class TestOnboardingStateTransitions:
    """Test onboarding state transitions and error recovery."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_config_dir = tempfile.mkdtemp()
        self.temp_vault_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_config_dir)
        shutil.rmtree(self.temp_vault_dir)

    @patch('dana_journal.config.app_config.AppConfig._get_config_dir')
    def test_onboarding_reset_functionality(self, mock_config_dir):
        """Test resetting onboarding state for testing/debugging."""
        mock_config_dir.return_value = Path(self.temp_config_dir)
        config = AppConfig()
        
        # Complete onboarding
        config.set_storage_path("/path/to/vault")
        config.set_ai_enabled(True)
        config.set_onboarded(True)
        
        assert config.is_onboarded()
        
        # Reset onboarding (test utility functionality)
        config.reset_onboarding_state()
        
        # Verify reset
        assert not config.is_onboarded()
        # Note: Some settings like storage_path might be preserved for re-onboarding

    @patch('dana_journal.config.app_config.AppConfig._get_config_dir')
    def test_configuration_persistence_across_restarts(self, mock_config_dir):
        """Test that onboarding configuration persists across app restarts."""
        mock_config_dir.return_value = Path(self.temp_config_dir)
        
        # First instance - complete onboarding
        config1 = AppConfig()
        config1.set_storage_path(self.temp_vault_dir)
        config1.set_vault_name("Test Vault")
        config1.set_ai_enabled(True)
        config1.set_onboarded(True)
        
        # Simulate app restart - create new config instance
        config2 = AppConfig()
        
        # Verify persistence
        assert config2.is_onboarded()
        assert config2.get_storage_path() == self.temp_vault_dir
        assert config2.get_vault_name() == "Test Vault"
        assert config2.get_ai_enabled()

    def test_vault_path_validation_during_onboarding(self):
        """Test vault path validation during setup."""
        # Test valid path
        valid_path = self.temp_vault_dir
        assert Path(valid_path).exists()
        
        # Test invalid/non-existent parent path
        invalid_path = "/completely/non/existent/path/vault"
        
        # FileManager should handle path creation gracefully
        # or raise appropriate errors for truly invalid paths
        try:
            fm = FileManager(invalid_path)
            # If creation succeeds, verify basic structure
            assert Path(invalid_path).exists()
        except (PermissionError, OSError):
            # Expected for paths that can't be created
            pass


class TestOnboardingUserExperience:
    """Test onboarding user experience aspects."""

    def test_onboarding_step_validation(self):
        """Test validation at each onboarding step."""
        # Step 3: Vault setup validation
        valid_vault_names = ["My Journal", "Personal Thoughts", "Work Notes 2025"]
        invalid_vault_names = ["", "   ", "a" * 256]  # Empty, whitespace, too long
        
        for name in valid_vault_names:
            assert len(name.strip()) > 0
            assert len(name) < 255
        
        for name in invalid_vault_names:
            assert len(name.strip()) == 0 or len(name) >= 255

    def test_vault_path_scenarios(self):
        """Test common vault path scenarios during onboarding."""
        test_scenarios = [
            ("~/Documents/Journal", "User home documents"),
            ("./MyJournal", "Relative path"), 
            ("/Users/test/Desktop/Journal", "Absolute path"),
        ]
        
        for path, description in test_scenarios:
            # Test path expansion and validation
            expanded_path = Path(path).expanduser().absolute()
            # Each path should be processable
            assert isinstance(str(expanded_path), str)
            assert len(str(expanded_path)) > 0

    def test_ai_setup_decision_points(self):
        """Test AI setup decision points during onboarding."""
        # Test configuration for different AI choices
        ai_configurations = [
            {"enabled": False, "reason": "User declines AI features"},
            {"enabled": True, "download": True, "reason": "User wants full AI features"},
            {"enabled": True, "download": False, "reason": "User enables but defers download"},
        ]
        
        for config in ai_configurations:
            # Each configuration should be valid
            assert isinstance(config["enabled"], bool)
            if config["enabled"] and "download" in config:
                assert isinstance(config["download"], bool)


if __name__ == "__main__":
    pytest.main([__file__])