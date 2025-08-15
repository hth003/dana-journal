"""
Storage Integration Service

Provides a high-level service layer that integrates the file storage system
with the main application, handling coordination between file operations,
auto-save, and UI updates.
"""

from datetime import date
from typing import Optional, Callable, Dict, Any, Set

from .file_manager import FileManager, JournalEntry
from .auto_save import AutoSaveManager, AutoSaveConfig, AutoSaveStatus
from config import app_config


class StorageIntegrationService:
    """High-level service for coordinating storage operations with the UI."""

    def __init__(self, vault_path: str, auto_save_config: AutoSaveConfig = None):
        """Initialize the integration service."""
        self.vault_path = vault_path

        # Initialize core components
        self.file_manager = FileManager(vault_path)
        self.auto_save_manager = AutoSaveManager(
            self.file_manager, auto_save_config or AutoSaveConfig()
        )
        self.auto_save_status = AutoSaveStatus(self.auto_save_manager)

        # State
        self.current_entry: Optional[JournalEntry] = None
        self.current_date: Optional[date] = None
        self._entry_cache: Dict[date, JournalEntry] = {}

        # Callbacks for UI updates
        self.on_entry_loaded: Optional[Callable[[date, JournalEntry], None]] = None
        self.on_entry_saved: Optional[Callable[[date, JournalEntry], None]] = None
        self.on_entry_created: Optional[Callable[[date, JournalEntry], None]] = None
        self.on_entry_deleted: Optional[Callable[[date], None]] = None
        self.on_entries_changed: Optional[Callable[[Set[date]], None]] = None
        self.on_save_status_changed: Optional[Callable[[bool], None]] = None

        # Set up auto-save callbacks
        self._setup_auto_save_callbacks()

        # Start auto-save
        self.auto_save_manager.start()

        # Scan existing files on initialization
        self._scan_existing_files()

    def _setup_auto_save_callbacks(self) -> None:
        """Set up callbacks for auto-save events."""

        def on_save_success(entry_date: date, entry: JournalEntry) -> None:
            self._entry_cache[entry_date] = entry
            if self.on_entry_saved:
                self.on_entry_saved(entry_date, entry)
            if self.on_save_status_changed:
                self.on_save_status_changed(False)  # Not dirty

        def on_save_error(entry_date: date, error: Exception) -> None:
            print(f"Auto-save error for {entry_date}: {error}")
            # Could trigger UI error notification here

        self.auto_save_manager.on_save_success = on_save_success
        self.auto_save_manager.on_save_error = on_save_error

    def _scan_existing_files(self) -> None:
        """Scan and index existing files."""
        try:
            count = self.file_manager.scan_existing_files()
            print(f"Scanned and indexed {count} existing entries")

            # Notify UI of available entries
            entry_dates = self.file_manager.get_entry_dates()
            if self.on_entries_changed:
                self.on_entries_changed(entry_dates)

        except Exception as e:
            print(f"Error scanning existing files: {e}")

    # Entry Management

    def load_entry(
        self, entry_date: date, use_cache: bool = True
    ) -> Optional[JournalEntry]:
        """Load an entry for the given date."""
        # Check cache first
        if use_cache and entry_date in self._entry_cache:
            entry = self._entry_cache[entry_date]
            self.current_entry = entry
            self.current_date = entry_date

            if self.on_entry_loaded:
                self.on_entry_loaded(entry_date, entry)

            return entry

        # Load from file system
        try:
            entry = self.file_manager.load_entry(entry_date)

            if entry:
                # Update cache
                self._entry_cache[entry_date] = entry
                self.current_entry = entry
                self.current_date = entry_date

                if self.on_entry_loaded:
                    self.on_entry_loaded(entry_date, entry)

                return entry
            else:
                return None

        except Exception as e:
            print(f"Error loading entry for {entry_date}: {e}")
            return None

    def create_entry(
        self, entry_date: date, title: str = None, content: str = ""
    ) -> Optional[JournalEntry]:
        """Create a new entry for the given date."""
        try:
            entry = self.file_manager.create_entry(entry_date, title, content)

            # Update cache and state
            self._entry_cache[entry_date] = entry
            self.current_entry = entry
            self.current_date = entry_date

            # Notify callbacks
            if self.on_entry_created:
                self.on_entry_created(entry_date, entry)

            # Update entries list
            entry_dates = self.file_manager.get_entry_dates()
            if self.on_entries_changed:
                self.on_entries_changed(entry_dates)

            return entry

        except Exception as e:
            print(f"Error creating entry for {entry_date}: {e}")
            return None

    def save_entry_now(
        self,
        entry_date: date,
        title: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Save an entry immediately (bypass auto-save)."""
        try:
            # Load existing entry or create new one
            entry = self.load_entry(entry_date, use_cache=False)

            if entry:
                # Update existing entry
                entry.title = title
                entry.content = content

                # Apply metadata
                if metadata:
                    if "tags" in metadata:
                        entry.tags = metadata["tags"]
                    if "mood_rating" in metadata:
                        entry.mood_rating = metadata["mood_rating"]
                    if "ai_reflection" in metadata:
                        entry.ai_reflection = metadata["ai_reflection"]

                success = self.file_manager.save_entry(entry)
            else:
                # Create new entry
                entry = self.create_entry(entry_date, title, content)
                success = entry is not None

                # Apply metadata if entry was created
                if success and entry and metadata:
                    if "tags" in metadata:
                        entry.tags = metadata["tags"]
                    if "mood_rating" in metadata:
                        entry.mood_rating = metadata["mood_rating"]
                    if "ai_reflection" in metadata:
                        entry.ai_reflection = metadata["ai_reflection"]

                    # Save again with metadata
                    success = self.file_manager.save_entry(entry)

            if success and entry:
                # Update cache
                self._entry_cache[entry_date] = entry

                # Notify callbacks
                if self.on_entry_saved:
                    self.on_entry_saved(entry_date, entry)

                if self.on_save_status_changed:
                    self.on_save_status_changed(False)  # Not dirty

            return success

        except Exception as e:
            print(f"Error saving entry for {entry_date}: {e}")
            return False

    def queue_auto_save(
        self,
        entry_date: date,
        title: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Queue an entry for auto-save."""
        self.auto_save_manager.queue_save(entry_date, title, content, metadata)

        # Notify that there are unsaved changes
        if self.on_save_status_changed:
            self.on_save_status_changed(True)  # Is dirty

    def delete_entry(self, entry_date: date) -> bool:
        """Delete an entry."""
        try:
            success = self.file_manager.delete_entry(entry_date)

            if success:
                # Remove from cache
                self._entry_cache.pop(entry_date, None)

                # Clear current entry if it was deleted
                if self.current_date == entry_date:
                    self.current_entry = None
                    self.current_date = None

                # Notify callbacks
                if self.on_entry_deleted:
                    self.on_entry_deleted(entry_date)

                # Update entries list
                entry_dates = self.file_manager.get_entry_dates()
                if self.on_entries_changed:
                    self.on_entries_changed(entry_dates)

            return success

        except Exception as e:
            print(f"Error deleting entry for {entry_date}: {e}")
            return False

    def rename_entry(self, old_date: date, new_date: date) -> bool:
        """Move an entry to a different date."""
        try:
            success = self.file_manager.rename_entry(old_date, new_date)

            if success:
                # Update cache
                if old_date in self._entry_cache:
                    entry = self._entry_cache.pop(old_date)
                    entry.date = new_date
                    self._entry_cache[new_date] = entry

                # Update current entry if it was renamed
                if self.current_date == old_date:
                    self.current_date = new_date
                    if self.current_entry:
                        self.current_entry.date = new_date

                # Notify callbacks
                if self.on_entry_deleted:
                    self.on_entry_deleted(old_date)

                entry = self._entry_cache.get(new_date)
                if entry and self.on_entry_created:
                    self.on_entry_created(new_date, entry)

                # Update entries list
                entry_dates = self.file_manager.get_entry_dates()
                if self.on_entries_changed:
                    self.on_entries_changed(entry_dates)

            return success

        except Exception as e:
            print(f"Error renaming entry from {old_date} to {new_date}: {e}")
            return False

    # Query Methods

    def get_entry_dates(self) -> Set[date]:
        """Get all dates that have entries."""
        return self.file_manager.get_entry_dates()

    def has_entry(self, entry_date: date) -> bool:
        """Check if an entry exists for the given date."""
        return entry_date in self.get_entry_dates()

    def search_entries(self, query: str, limit: int = 50) -> list[JournalEntry]:
        """Search entries by content or title."""
        return self.file_manager.search_entries(query, limit)

    def get_entries_in_range(
        self, start_date: date, end_date: date
    ) -> list[JournalEntry]:
        """Get all entries within a date range."""
        return self.file_manager.get_entries_in_range(start_date, end_date)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about journal entries."""
        return self.file_manager.get_statistics()

    # Auto-Save Management

    def get_auto_save_status(self) -> Dict[str, Any]:
        """Get auto-save status information."""
        return self.auto_save_status.get_status()

    def get_entry_auto_save_status(self, entry_date: date) -> Dict[str, Any]:
        """Get auto-save status for a specific entry."""
        return self.auto_save_status.get_entry_status(entry_date)

    def force_save_all(self) -> Dict[date, bool]:
        """Force immediate save of all pending entries."""
        return self.auto_save_manager.force_save_all()

    def has_pending_saves(self) -> bool:
        """Check if there are pending auto-saves."""
        return self.auto_save_manager.has_pending_saves()

    # Configuration

    def update_auto_save_config(self, **config_updates) -> None:
        """Update auto-save configuration."""
        config = self.auto_save_manager.config

        for key, value in config_updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

    def set_auto_save_enabled(self, enabled: bool) -> None:
        """Enable or disable auto-save."""
        self.auto_save_manager.config.enabled = enabled

    # Cleanup

    def shutdown(self) -> None:
        """Shutdown the storage service and save pending changes."""
        try:
            # Force save all pending changes
            if self.has_pending_saves():
                print("Saving pending changes before shutdown...")
                results = self.force_save_all()
                failed_saves = [
                    date for date, success in results.items() if not success
                ]
                if failed_saves:
                    print(f"Warning: Failed to save entries for dates: {failed_saves}")

            # Stop auto-save
            self.auto_save_manager.stop()

            print("Storage service shutdown complete")

        except Exception as e:
            print(f"Error during storage service shutdown: {e}")

    # Maintenance and Validation

    def validate_vault(self) -> Dict[str, Any]:
        """Validate the vault structure and integrity."""
        return self.file_manager.validate_vault()

    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        return self.file_manager.backup_database(backup_path)

    def refresh_entries(self) -> int:
        """Refresh entry list from file system."""
        try:
            count = self.file_manager.scan_existing_files()

            # Clear cache to force reload
            self._entry_cache.clear()

            # Notify UI of updated entries
            entry_dates = self.file_manager.get_entry_dates()
            if self.on_entries_changed:
                self.on_entries_changed(entry_dates)

            return count

        except Exception as e:
            print(f"Error refreshing entries: {e}")
            return 0


# Factory function for easy integration
def create_storage_service(
    vault_path: str = None, auto_save_config: AutoSaveConfig = None
) -> StorageIntegrationService:
    """
    Create a storage integration service.

    Args:
        vault_path: Path to vault directory (uses config if not provided)
        auto_save_config: Auto-save configuration

    Returns:
        Configured StorageIntegrationService
    """
    if vault_path is None:
        vault_path = app_config.get_storage_path()
        if not vault_path:
            raise ValueError(
                "No vault path configured. Please complete onboarding first."
            )

    return StorageIntegrationService(vault_path, auto_save_config)
