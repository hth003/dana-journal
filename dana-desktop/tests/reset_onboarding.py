#!/usr/bin/env uv run python
"""
Script to reset onboarding state for testing
"""

import json
from pathlib import Path


def reset_onboarding():
    """Reset the onboarding state to allow testing again."""
    # Check both old and new config directories
    old_config_dir = Path.home() / ".journal_vault"
    new_config_dir = Path.home() / ".dana_journal"

    # Use new directory if it exists, otherwise old directory
    config_dir = new_config_dir if new_config_dir.exists() else old_config_dir
    config_file = config_dir / "config.json"

    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)

            # Remove onboarding flag
            if "onboarded" in config_data:
                del config_data["onboarded"]

            # Remove storage path
            if "storage_path" in config_data:
                del config_data["storage_path"]

            # Save updated config
            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)

            print("✅ Onboarding state reset successfully!")
            print("You can now test the folder selection again.")

        except Exception as e:
            print(f"❌ Error resetting onboarding: {e}")
    else:
        print("ℹ️  No config file found - onboarding is already reset.")


if __name__ == "__main__":
    reset_onboarding()
