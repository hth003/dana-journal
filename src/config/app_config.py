"""
Application Configuration Management

Handles saving and loading of user preferences, onboarding status,
and other application configuration data.
"""

import json
import shutil
from typing import Dict, Any, Optional
from pathlib import Path


class AppConfig:
    """Manages application configuration and preferences."""

    def __init__(self):
        self.old_config_dir = Path.home() / ".journal_vault"
        self.config_dir = Path.home() / ".dana_journal"
        self.config_file = self.config_dir / "config.json"
        self._config_data = {}

        # Handle migration from old directory
        self._migrate_config_if_needed()

        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)

        # Load existing config
        self._load_config()

    def _migrate_config_if_needed(self) -> None:
        """Migrate configuration from old .journal_vault directory to .dana_journal."""
        if self.old_config_dir.exists() and not self.config_dir.exists():
            try:
                # Copy entire directory to new location
                shutil.copytree(self.old_config_dir, self.config_dir)
                print(
                    f"Migrated configuration from {self.old_config_dir} to {self.config_dir}"
                )
            except Exception as e:
                print(f"Error migrating config: {e}")
                # Create new config directory if migration fails
                self.config_dir.mkdir(exist_ok=True)

    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self._config_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
                self._config_data = {}
        else:
            self._config_data = {}

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self._config_data, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")

    def is_onboarded(self) -> bool:
        """Check if user has completed onboarding."""
        return self._config_data.get("onboarded", False)

    def set_onboarded(self, onboarded: bool = True) -> None:
        """Set onboarding status."""
        self._config_data["onboarded"] = onboarded
        self._save_config()

    def get_storage_path(self) -> Optional[str]:
        """Get the configured storage path."""
        return self._config_data.get("storage_path")

    def set_storage_path(self, path: str) -> None:
        """Set the storage path."""
        self._config_data["storage_path"] = path
        self._save_config()

    def get_vault_name(self) -> Optional[str]:
        """Get the configured vault name."""
        return self._config_data.get("vault_name")

    def set_vault_name(self, name: str) -> None:
        """Set the vault name."""
        self._config_data["vault_name"] = name
        self._save_config()

    def is_ai_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self._config_data.get("ai_enabled", False)

    def set_ai_enabled(self, enabled: bool) -> None:
        """Set AI features enabled status."""
        self._config_data["ai_enabled"] = enabled
        self._save_config()

    def is_ai_model_downloaded(self) -> bool:
        """Check if AI model has been downloaded."""
        return self._config_data.get("ai_model_downloaded", False)

    def set_ai_model_downloaded(self, downloaded: bool) -> None:
        """Set AI model downloaded status."""
        self._config_data["ai_model_downloaded"] = downloaded
        self._save_config()

    def was_ai_skipped_during_onboarding(self) -> bool:
        """Check if AI was skipped during onboarding."""
        return self._config_data.get("ai_skipped_during_onboarding", False)

    def set_ai_skipped_during_onboarding(self, skipped: bool) -> None:
        """Set AI skipped during onboarding status."""
        self._config_data["ai_skipped_during_onboarding"] = skipped
        self._save_config()

    def get_ai_model_path(self) -> Optional[str]:
        """Get the path to the AI model file."""
        return self._config_data.get("ai_model_path")

    def set_ai_model_path(self, path: str) -> None:
        """Set the AI model file path."""
        self._config_data["ai_model_path"] = path
        self._save_config()

    def get_ai_inference_settings(self) -> Dict[str, Any]:
        """Get AI inference settings."""
        return self._config_data.get(
            "ai_inference_settings",
            {
                "n_threads": 4,
                "temperature": 0.7,
                "max_tokens": 512,
                "cache_enabled": True,
                "cache_expiry_hours": 168,  # 1 week
                "auto_load_model": True,
            },
        )

    def set_ai_inference_settings(self, settings: Dict[str, Any]) -> None:
        """Set AI inference settings."""
        self._config_data["ai_inference_settings"] = settings
        self._save_config()

    def get_ai_service_status(self) -> Dict[str, Any]:
        """Get AI service status information."""
        return self._config_data.get(
            "ai_service_status",
            {
                "last_model_load_success": None,
                "last_model_load_error": None,
                "model_load_count": 0,
                "successful_generations": 0,
                "failed_generations": 0,
            },
        )

    def update_ai_service_status(self, status_updates: Dict[str, Any]) -> None:
        """Update AI service status."""
        current_status = self.get_ai_service_status()
        current_status.update(status_updates)
        self._config_data["ai_service_status"] = current_status
        self._save_config()

    def get_window_state(self) -> Dict[str, Any]:
        """Get saved window state."""
        return self._config_data.get(
            "window_state", {"width": 1400, "height": 900, "maximized": False}
        )

    def set_window_state(
        self, width: int, height: int, maximized: bool = False
    ) -> None:
        """Save window state."""
        self._config_data["window_state"] = {
            "width": width,
            "height": height,
            "maximized": maximized,
        }
        self._save_config()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference value."""
        preferences = self._config_data.get("preferences", {})
        return preferences.get(key, default)

    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference value."""
        if "preferences" not in self._config_data:
            self._config_data["preferences"] = {}
        self._config_data["preferences"][key] = value
        self._save_config()

    def clear_config(self) -> None:
        """Clear all configuration data."""
        self._config_data = {}
        if self.config_file.exists():
            self.config_file.unlink()

    def export_config(self, export_path: str) -> bool:
        """Export configuration to a file."""
        try:
            export_file = Path(export_path)
            with open(export_file, "w") as f:
                json.dump(self._config_data, f, indent=2)
            return True
        except IOError:
            return False

    def import_config(self, import_path: str) -> bool:
        """Import configuration from a file."""
        try:
            import_file = Path(import_path)
            if import_file.exists():
                with open(import_file, "r") as f:
                    imported_data = json.load(f)
                self._config_data.update(imported_data)
                self._save_config()
                return True
        except (json.JSONDecodeError, IOError):
            pass
        return False


# Global configuration instance
app_config = AppConfig()
