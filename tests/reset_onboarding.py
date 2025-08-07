#!/usr/bin/env uv run python
"""
Script to reset onboarding state for testing
"""

import os
import json
from pathlib import Path

def reset_onboarding():
    """Reset the onboarding state to allow testing again."""
    config_dir = Path.home() / ".journal_vault"
    config_file = config_dir / "config.json"
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Remove onboarding flag
            if 'onboarded' in config_data:
                del config_data['onboarded']
            
            # Remove storage path
            if 'storage_path' in config_data:
                del config_data['storage_path']
            
            # Save updated config
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print("✅ Onboarding state reset successfully!")
            print("You can now test the folder selection again.")
            
        except Exception as e:
            print(f"❌ Error resetting onboarding: {e}")
    else:
        print("ℹ️  No config file found - onboarding is already reset.")

if __name__ == "__main__":
    reset_onboarding() 