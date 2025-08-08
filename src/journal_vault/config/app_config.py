"""
Application Configuration Management

Handles saving and loading of user preferences, onboarding status,
and other application configuration data.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class AppConfig:
    """Manages application configuration and preferences."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".journal_vault"
        self.config_file = self.config_dir / "config.json"
        self._config_data = {}
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Load existing config
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}")
                self._config_data = {}
        else:
            self._config_data = {}
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config_data, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")
    
    def is_onboarded(self) -> bool:
        """Check if user has completed onboarding."""
        return self._config_data.get('onboarded', False)
    
    def set_onboarded(self, onboarded: bool = True) -> None:
        """Set onboarding status."""
        self._config_data['onboarded'] = onboarded
        self._save_config()
    
    def get_storage_path(self) -> Optional[str]:
        """Get the configured storage path."""
        return self._config_data.get('storage_path')
    
    def set_storage_path(self, path: str) -> None:
        """Set the storage path."""
        self._config_data['storage_path'] = path
        self._save_config()
    
    def get_vault_name(self) -> Optional[str]:
        """Get the configured vault name."""
        return self._config_data.get('vault_name')
    
    def set_vault_name(self, name: str) -> None:
        """Set the vault name."""
        self._config_data['vault_name'] = name
        self._save_config()
    
    def is_ai_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self._config_data.get('ai_enabled', False)
    
    def set_ai_enabled(self, enabled: bool) -> None:
        """Set AI features enabled status."""
        self._config_data['ai_enabled'] = enabled
        self._save_config()
    
    def is_ai_model_downloaded(self) -> bool:
        """Check if AI model has been downloaded."""
        return self._config_data.get('ai_model_downloaded', False)
    
    def set_ai_model_downloaded(self, downloaded: bool) -> None:
        """Set AI model downloaded status."""
        self._config_data['ai_model_downloaded'] = downloaded
        self._save_config()
    
    def was_ai_skipped_during_onboarding(self) -> bool:
        """Check if AI was skipped during onboarding."""
        return self._config_data.get('ai_skipped_during_onboarding', False)
    
    def set_ai_skipped_during_onboarding(self, skipped: bool) -> None:
        """Set AI skipped during onboarding status."""
        self._config_data['ai_skipped_during_onboarding'] = skipped
        self._save_config()
    
    def get_ai_model_path(self) -> Optional[str]:
        """Get the path to the AI model file."""
        return self._config_data.get('ai_model_path')
    
    def set_ai_model_path(self, path: str) -> None:
        """Set the AI model file path."""
        self._config_data['ai_model_path'] = path
        self._save_config()
    
    
    def get_window_state(self) -> Dict[str, Any]:
        """Get saved window state."""
        return self._config_data.get('window_state', {
            'width': 1400,
            'height': 900,
            'maximized': False
        })
    
    def set_window_state(self, width: int, height: int, maximized: bool = False) -> None:
        """Save window state."""
        self._config_data['window_state'] = {
            'width': width,
            'height': height,
            'maximized': maximized
        }
        self._save_config()
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference value."""
        preferences = self._config_data.get('preferences', {})
        return preferences.get(key, default)
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference value."""
        if 'preferences' not in self._config_data:
            self._config_data['preferences'] = {}
        self._config_data['preferences'][key] = value
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
            with open(export_file, 'w') as f:
                json.dump(self._config_data, f, indent=2)
            return True
        except IOError:
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from a file."""
        try:
            import_file = Path(import_path)
            if import_file.exists():
                with open(import_file, 'r') as f:
                    imported_data = json.load(f)
                self._config_data.update(imported_data)
                self._save_config()
                return True
        except (json.JSONDecodeError, IOError):
            pass
        return False


# Global configuration instance
app_config = AppConfig()