"""
File Storage and Data Management Module

Provides comprehensive file-based storage for journal entries with:
- File system operations (CRUD) for markdown files
- Auto-save functionality with debouncing
- SQLite indexing for fast lookups
- YAML frontmatter for metadata
- Directory structure management
- File watching and validation

Core Components:
- FileManager: Main storage operations
- AutoSaveManager: Debounced auto-saving
- JournalEntry: Data model for entries
- AutoSaveConfig: Configuration for auto-save
"""

from .file_manager import FileManager, JournalEntry
from .auto_save import (
    AutoSaveManager,
    AutoSaveConfig,
    AutoSaveStatus,
    create_auto_save_manager,
    setup_auto_save_callbacks,
)

# Export all public classes and functions
__all__ = [
    # Core storage classes
    "FileManager",
    "JournalEntry",
    # Auto-save functionality
    "AutoSaveManager",
    "AutoSaveConfig",
    "AutoSaveStatus",
    # Utility functions
    "create_auto_save_manager",
    "setup_auto_save_callbacks",
    # Factory functions
    "create_file_manager",
    "create_storage_system",
]


def create_file_manager(vault_path: str) -> FileManager:
    """
    Create a FileManager instance for the given vault path.

    Args:
        vault_path: Path to the journal vault directory

    Returns:
        Configured FileManager instance
    """
    return FileManager(vault_path)


def create_storage_system(
    vault_path: str, auto_save_config: AutoSaveConfig = None
) -> tuple[FileManager, AutoSaveManager]:
    """
    Create a complete storage system with file manager and auto-save.

    Args:
        vault_path: Path to the journal vault directory
        auto_save_config: Optional auto-save configuration

    Returns:
        Tuple of (FileManager, AutoSaveManager)
    """
    file_manager = FileManager(vault_path)
    auto_save_manager = AutoSaveManager(file_manager, auto_save_config)
    return file_manager, auto_save_manager
