"""
Auto-save system for journal entries.

Provides automatic saving functionality with debouncing to prevent
excessive file writes while ensuring data persistence.
"""

import asyncio
import threading
from datetime import datetime, date
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

from .file_manager import FileManager, JournalEntry


@dataclass
class AutoSaveConfig:
    """Configuration for auto-save behavior."""
    
    # Auto-save interval in seconds
    save_interval: int = 30
    
    # Maximum time to wait before forcing a save (seconds)
    max_delay: int = 300  # 5 minutes
    
    # Minimum characters changed before triggering save
    min_changes: int = 10
    
    # Enable/disable auto-save
    enabled: bool = True


class AutoSaveManager:
    """Manages automatic saving of journal entries with debouncing."""
    
    def __init__(self, file_manager: FileManager, config: AutoSaveConfig = None):
        """Initialize the auto-save manager."""
        self.file_manager = file_manager
        self.config = config or AutoSaveConfig()
        
        # State tracking
        self._pending_saves: Dict[date, Dict[str, Any]] = {}
        self._last_save_time: Dict[date, datetime] = {}
        self._save_timers: Dict[date, threading.Timer] = {}
        self._is_running = False
        
        # Callbacks
        self.on_save_success: Optional[Callable[[date, JournalEntry], None]] = None
        self.on_save_error: Optional[Callable[[date, Exception], None]] = None
        
        # Thread lock for thread safety
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Start the auto-save system."""
        with self._lock:
            self._is_running = True
    
    def stop(self) -> None:
        """Stop the auto-save system and cancel pending saves."""
        with self._lock:
            self._is_running = False
            
            # Cancel all pending timers
            for timer in self._save_timers.values():
                timer.cancel()
            
            self._save_timers.clear()
            self._pending_saves.clear()
    
    def queue_save(self, entry_date: date, title: str, content: str, 
                  metadata: Dict[str, Any] = None) -> None:
        """Queue a save operation for the given entry."""
        if not self.config.enabled or not self._is_running:
            return
        
        current_time = datetime.now()
        
        with self._lock:
            # Store the pending save data
            self._pending_saves[entry_date] = {
                'title': title,
                'content': content,
                'metadata': metadata or {},
                'queued_at': current_time,
                'content_hash': hash(content)  # Simple hash for change detection
            }
            
            # Cancel existing timer for this date
            if entry_date in self._save_timers:
                self._save_timers[entry_date].cancel()
            
            # Determine save delay
            last_save = self._last_save_time.get(entry_date)
            
            if last_save is None:
                # First save - use shorter delay
                delay = min(self.config.save_interval, 10)
            else:
                # Check if max delay exceeded
                time_since_last = (current_time - last_save).total_seconds()
                if time_since_last >= self.config.max_delay:
                    delay = 0  # Save immediately
                else:
                    delay = self.config.save_interval
            
            # Schedule the save
            timer = threading.Timer(delay, self._perform_save, args=[entry_date])
            self._save_timers[entry_date] = timer
            timer.start()
    
    def force_save(self, entry_date: date) -> bool:
        """Force an immediate save for the given date."""
        with self._lock:
            if entry_date in self._save_timers:
                self._save_timers[entry_date].cancel()
                del self._save_timers[entry_date]
            
            return self._perform_save(entry_date)
    
    def force_save_all(self) -> Dict[date, bool]:
        """Force immediate save for all pending entries."""
        results = {}
        
        with self._lock:
            pending_dates = list(self._pending_saves.keys())
        
        for entry_date in pending_dates:
            results[entry_date] = self.force_save(entry_date)
        
        return results
    
    def _perform_save(self, entry_date: date) -> bool:
        """Perform the actual save operation."""
        try:
            with self._lock:
                if entry_date not in self._pending_saves:
                    return True  # Nothing to save
                
                save_data = self._pending_saves[entry_date]
                del self._pending_saves[entry_date]
                
                # Remove timer reference
                if entry_date in self._save_timers:
                    del self._save_timers[entry_date]
            
            # Check if content has meaningful changes
            if not self._has_meaningful_changes(save_data['content']):
                return True  # Skip save for trivial changes
            
            # Load existing entry or create new one
            existing_entry = self.file_manager.load_entry(entry_date)
            
            if existing_entry:
                # Update existing entry
                existing_entry.title = save_data['title']
                existing_entry.content = save_data['content']
                
                # Apply metadata updates
                metadata = save_data.get('metadata', {})
                if 'tags' in metadata:
                    existing_entry.tags = metadata['tags']
                if 'mood_rating' in metadata:
                    existing_entry.mood_rating = metadata['mood_rating']
                if 'ai_reflection' in metadata:
                    existing_entry.ai_reflection = metadata['ai_reflection']
                
                success = self.file_manager.save_entry(existing_entry)
                saved_entry = existing_entry
            else:
                # Create new entry
                saved_entry = self.file_manager.create_entry(
                    entry_date=entry_date,
                    title=save_data['title'],
                    content=save_data['content']
                )
                
                # Apply metadata
                metadata = save_data.get('metadata', {})
                if metadata:
                    if 'tags' in metadata:
                        saved_entry.tags = metadata['tags']
                    if 'mood_rating' in metadata:
                        saved_entry.mood_rating = metadata['mood_rating']
                    if 'ai_reflection' in metadata:
                        saved_entry.ai_reflection = metadata['ai_reflection']
                    
                    # Save again with metadata
                    success = self.file_manager.save_entry(saved_entry)
                else:
                    success = True
            
            # Update last save time
            with self._lock:
                self._last_save_time[entry_date] = datetime.now()
            
            # Trigger success callback
            if success and self.on_save_success:
                try:
                    self.on_save_success(entry_date, saved_entry)
                except Exception as callback_error:
                    print(f"Error in save success callback: {callback_error}")
            
            return success
            
        except Exception as e:
            print(f"Error performing auto-save for {entry_date}: {e}")
            
            # Trigger error callback
            if self.on_save_error:
                try:
                    self.on_save_error(entry_date, e)
                except Exception as callback_error:
                    print(f"Error in save error callback: {callback_error}")
            
            return False
    
    def _has_meaningful_changes(self, content: str) -> bool:
        """Check if content has meaningful changes worth saving."""
        if not content or content.isspace():
            return False
        
        # Check minimum length
        if len(content.strip()) < self.config.min_changes:
            return False
        
        return True
    
    def get_pending_saves(self) -> Dict[date, Dict[str, Any]]:
        """Get information about pending saves."""
        with self._lock:
            return {
                entry_date: {
                    'queued_at': data['queued_at'],
                    'content_length': len(data['content']),
                    'has_metadata': bool(data.get('metadata'))
                }
                for entry_date, data in self._pending_saves.items()
            }
    
    def has_pending_saves(self) -> bool:
        """Check if there are any pending saves."""
        with self._lock:
            return len(self._pending_saves) > 0
    
    def get_last_save_time(self, entry_date: date) -> Optional[datetime]:
        """Get the last save time for a specific entry."""
        with self._lock:
            return self._last_save_time.get(entry_date)
    
    def clear_save_history(self, entry_date: date = None) -> None:
        """Clear save history for a specific date or all dates."""
        with self._lock:
            if entry_date is None:
                self._last_save_time.clear()
            else:
                self._last_save_time.pop(entry_date, None)


class AutoSaveStatus:
    """Provides status information about auto-save operations."""
    
    def __init__(self, auto_save_manager: AutoSaveManager):
        self.auto_save_manager = auto_save_manager
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive auto-save status."""
        pending_saves = self.auto_save_manager.get_pending_saves()
        
        return {
            'enabled': self.auto_save_manager.config.enabled,
            'running': self.auto_save_manager._is_running,
            'save_interval': self.auto_save_manager.config.save_interval,
            'pending_saves_count': len(pending_saves),
            'pending_saves': pending_saves,
            'config': {
                'save_interval': self.auto_save_manager.config.save_interval,
                'max_delay': self.auto_save_manager.config.max_delay,
                'min_changes': self.auto_save_manager.config.min_changes,
                'enabled': self.auto_save_manager.config.enabled
            }
        }
    
    def get_entry_status(self, entry_date: date) -> Dict[str, Any]:
        """Get auto-save status for a specific entry."""
        pending_saves = self.auto_save_manager.get_pending_saves()
        last_save = self.auto_save_manager.get_last_save_time(entry_date)
        
        return {
            'has_pending_save': entry_date in pending_saves,
            'pending_info': pending_saves.get(entry_date),
            'last_save_time': last_save,
            'time_since_last_save': (
                (datetime.now() - last_save).total_seconds() 
                if last_save else None
            )
        }


# Utility functions for integration

def create_auto_save_manager(vault_path: str, config: AutoSaveConfig = None) -> AutoSaveManager:
    """Create and configure an auto-save manager."""
    from .file_manager import FileManager
    
    file_manager = FileManager(vault_path)
    return AutoSaveManager(file_manager, config)


def setup_auto_save_callbacks(auto_save_manager: AutoSaveManager, 
                             on_success: Callable = None,
                             on_error: Callable = None) -> None:
    """Set up callbacks for auto-save events."""
    if on_success:
        auto_save_manager.on_save_success = on_success
    
    if on_error:
        auto_save_manager.on_save_error = on_error