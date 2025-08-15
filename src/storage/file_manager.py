"""
File-based storage system for journal entries.

Handles creation, reading, updating, and deletion of markdown journal files
with YAML frontmatter. Manages the directory structure and file organization.
"""

import sqlite3
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import yaml
import json
from dataclasses import dataclass


@dataclass
class JournalEntry:
    """Represents a journal entry with metadata."""

    # Core content
    title: str
    content: str

    # Metadata
    created_at: datetime
    modified_at: datetime
    date: date  # The journal date (different from created_at)

    # Optional metadata
    tags: List[str] = None
    word_count: int = 0
    mood_rating: Optional[int] = None

    # AI metadata
    ai_reflection: Optional[Dict[str, Any]] = None

    # System metadata
    version: int = 1
    file_path: Optional[Path] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []
        if self.word_count == 0:
            self.word_count = len(self.content.split()) if self.content else 0


class FileManager:
    """Manages file-based storage for journal entries."""

    @staticmethod
    def is_existing_vault(path: str) -> bool:
        """Check if a directory contains an existing Journal Vault.

        Args:
            path: Directory path to check

        Returns:
            True if the path contains a Journal Vault, False otherwise
        """
        try:
            vault_path = Path(path)
            metadata_path = vault_path / ".dana_journal"
            return metadata_path.exists() and metadata_path.is_dir()
        except Exception:
            # If any error occurs during detection, assume it's an existing vault (safer)
            return True

    def __init__(self, vault_path: str):
        """Initialize the file manager with vault path."""
        self.vault_path = Path(vault_path)
        self.entries_path = self.vault_path / "entries"
        self.metadata_path = self.vault_path / ".dana_journal"
        self.db_path = self.metadata_path / "index.sqlite"
        self.ai_cache_path = self.metadata_path / "ai_cache"

        # Ensure directories exist
        self._setup_directories()

        # Initialize database
        self._init_database()

    def _setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.vault_path,
            self.entries_path,
            self.metadata_path,
            self.ai_cache_path,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _init_database(self) -> None:
        """Initialize SQLite database for indexing."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    title TEXT,
                    word_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    tags TEXT,  -- JSON array
                    mood_rating INTEGER,
                    has_ai_reflection BOOLEAN DEFAULT FALSE,
                    content_hash TEXT,
                    version INTEGER DEFAULT 1
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_date ON entries(date)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_modified ON entries(modified_at)
            """
            )

            conn.commit()

    def _get_entry_file_path(self, entry_date: date) -> Path:
        """Get the file path for a journal entry based on date."""
        year_month_dir = (
            self.entries_path / str(entry_date.year) / f"{entry_date.month:02d}"
        )
        year_month_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{entry_date.strftime('%Y-%m-%d')}.md"
        return year_month_dir / filename

    def _content_hash(self, content: str) -> str:
        """Generate hash for content change detection."""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _parse_frontmatter(self, file_content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown file."""
        if not file_content.startswith("---\n"):
            return {}, file_content

        try:
            # Find the end of frontmatter
            end_marker = file_content.find("\n---\n", 4)
            if end_marker == -1:
                return {}, file_content

            # Extract frontmatter and content
            frontmatter_text = file_content[4:end_marker]
            content = file_content[end_marker + 5 :].strip()

            # Parse YAML
            frontmatter = yaml.safe_load(frontmatter_text) or {}
            return frontmatter, content

        except yaml.YAMLError as e:
            print(f"Error parsing YAML frontmatter: {e}")
            return {}, file_content

    def _create_frontmatter(self, entry: JournalEntry) -> str:
        """Create YAML frontmatter from entry metadata."""
        metadata = {
            "title": entry.title,
            "created_at": entry.created_at.isoformat(),
            "modified_at": entry.modified_at.isoformat(),
            "tags": entry.tags,
            "word_count": entry.word_count,
            "version": entry.version,
        }

        # Add optional fields
        if entry.mood_rating is not None:
            metadata["mood_rating"] = entry.mood_rating

        if entry.ai_reflection:
            metadata["ai_reflection"] = entry.ai_reflection

        # Convert to YAML
        yaml_content = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        return f"---\n{yaml_content}---\n\n"

    def create_entry(
        self, entry_date: date, title: str = None, content: str = ""
    ) -> JournalEntry:
        """Create a new journal entry."""
        if title is None:
            title = entry_date.strftime('%b %d, %Y')  # Friendly date format: Aug 14, 2025

        now = datetime.now()
        entry = JournalEntry(
            title=title,
            content=content,
            created_at=now,
            modified_at=now,
            date=entry_date,
            tags=[],
            word_count=len(content.split()) if content else 0,
        )

        # Set file path
        entry.file_path = self._get_entry_file_path(entry_date)

        # Save to file system
        self._save_entry_to_file(entry)

        # Update database index
        self._update_database_index(entry)

        return entry

    def load_entry(self, entry_date: date) -> Optional[JournalEntry]:
        """Load a journal entry for the given date."""
        file_path = self._get_entry_file_path(entry_date)

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Parse frontmatter and content
            frontmatter, content = self._parse_frontmatter(file_content)

            # Create entry object
            entry = JournalEntry(
                title=frontmatter.get(
                    "title", f"Journal Entry - {entry_date.strftime('%B %d, %Y')}"
                ),
                content=content,
                created_at=datetime.fromisoformat(
                    frontmatter.get("created_at", datetime.now().isoformat())
                ),
                modified_at=datetime.fromisoformat(
                    frontmatter.get("modified_at", datetime.now().isoformat())
                ),
                date=entry_date,
                tags=frontmatter.get("tags", []),
                word_count=frontmatter.get(
                    "word_count", len(content.split()) if content else 0
                ),
                mood_rating=frontmatter.get("mood_rating"),
                ai_reflection=frontmatter.get("ai_reflection"),
                version=frontmatter.get("version", 1),
                file_path=file_path,
            )

            return entry

        except Exception as e:
            print(f"Error loading entry for {entry_date}: {e}")
            return None

    def save_entry(self, entry: JournalEntry) -> bool:
        """Save an existing journal entry."""
        if entry.file_path is None:
            entry.file_path = self._get_entry_file_path(entry.date)

        # Update modification time and word count
        entry.modified_at = datetime.now()
        entry.word_count = len(entry.content.split()) if entry.content else 0

        try:
            # Save to file system
            self._save_entry_to_file(entry)

            # Update database index
            self._update_database_index(entry)

            return True

        except Exception as e:
            print(f"Error saving entry: {e}")
            return False

    def _save_entry_to_file(self, entry: JournalEntry) -> None:
        """Save entry to markdown file with frontmatter."""
        # Create frontmatter
        frontmatter = self._create_frontmatter(entry)

        # Combine frontmatter and content
        file_content = frontmatter + entry.content

        # Write to file
        with open(entry.file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

    def _update_database_index(self, entry: JournalEntry) -> None:
        """Update the database index with entry metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO entries (
                    date, file_path, title, word_count, created_at, modified_at,
                    tags, mood_rating, has_ai_reflection, content_hash, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry.date.isoformat(),
                    str(entry.file_path),
                    entry.title,
                    entry.word_count,
                    entry.created_at.isoformat(),
                    entry.modified_at.isoformat(),
                    json.dumps(entry.tags),
                    entry.mood_rating,
                    entry.ai_reflection is not None,
                    self._content_hash(entry.content),
                    entry.version,
                ),
            )
            conn.commit()

    def delete_entry(self, entry_date: date) -> bool:
        """Delete a journal entry."""
        file_path = self._get_entry_file_path(entry_date)

        try:
            # Remove file if it exists
            if file_path.exists():
                file_path.unlink()

            # Remove from database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM entries WHERE date = ?", (entry_date.isoformat(),)
                )
                conn.commit()

            return True

        except Exception as e:
            print(f"Error deleting entry for {entry_date}: {e}")
            return False

    def rename_entry(self, old_date: date, new_date: date) -> bool:
        """Rename/move an entry to a different date."""
        old_entry = self.load_entry(old_date)
        if not old_entry:
            return False

        try:
            # Update entry date and title
            old_entry.date = new_date
            old_entry.title = new_date.strftime('%b %d, %Y')  # Update title to match new date
            old_entry.modified_at = datetime.now()

            # Save to new location
            old_entry.file_path = self._get_entry_file_path(new_date)
            self._save_entry_to_file(old_entry)
            self._update_database_index(old_entry)

            # Delete old entry
            self.delete_entry(old_date)

            return True

        except Exception as e:
            print(f"Error renaming entry from {old_date} to {new_date}: {e}")
            return False

    def get_entry_dates(self) -> Set[date]:
        """Get all dates that have journal entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT date FROM entries")
                dates = {date.fromisoformat(row[0]) for row in cursor.fetchall()}
                return dates
        except Exception as e:
            print(f"Error getting entry dates: {e}")
            return set()

    def get_entries_in_range(
        self, start_date: date, end_date: date
    ) -> List[JournalEntry]:
        """Get all entries within a date range."""
        entries = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT date FROM entries 
                    WHERE date BETWEEN ? AND ? 
                    ORDER BY date DESC
                """,
                    (start_date.isoformat(), end_date.isoformat()),
                )

                for row in cursor.fetchall():
                    entry_date = date.fromisoformat(row[0])
                    entry = self.load_entry(entry_date)
                    if entry:
                        entries.append(entry)

        except Exception as e:
            print(f"Error getting entries in range: {e}")

        return entries

    def search_entries(self, query: str, limit: int = 50) -> List[JournalEntry]:
        """Search entries by content or title (basic implementation)."""
        # This is a basic implementation - can be enhanced with full-text search
        entries = []
        query_lower = query.lower()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT date FROM entries 
                    WHERE LOWER(title) LIKE ? 
                    ORDER BY modified_at DESC 
                    LIMIT ?
                """,
                    (f"%{query_lower}%", limit),
                )

                for row in cursor.fetchall():
                    entry_date = date.fromisoformat(row[0])
                    entry = self.load_entry(entry_date)
                    if entry and (
                        query_lower in entry.content.lower()
                        or query_lower in entry.title.lower()
                    ):
                        entries.append(entry)

        except Exception as e:
            print(f"Error searching entries: {e}")

        return entries

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the journal entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT 
                        COUNT(*) as total_entries,
                        SUM(word_count) as total_words,
                        AVG(word_count) as avg_words_per_entry,
                        MIN(date) as first_entry_date,
                        MAX(date) as last_entry_date,
                        COUNT(CASE WHEN has_ai_reflection THEN 1 END) as entries_with_ai
                    FROM entries
                """
                )

                row = cursor.fetchone()
                if row:
                    return {
                        "total_entries": row[0] or 0,
                        "total_words": row[1] or 0,
                        "avg_words_per_entry": round(row[2] or 0, 1),
                        "first_entry_date": row[3],
                        "last_entry_date": row[4],
                        "entries_with_ai": row[5] or 0,
                    }

        except Exception as e:
            print(f"Error getting statistics: {e}")

        return {
            "total_entries": 0,
            "total_words": 0,
            "avg_words_per_entry": 0,
            "first_entry_date": None,
            "last_entry_date": None,
            "entries_with_ai": 0,
        }

    def scan_existing_files(self) -> int:
        """Scan the entries directory and update the database index."""
        count = 0

        try:
            # Find all markdown files in entries directory
            for md_file in self.entries_path.glob("*/*/*.md"):
                try:
                    # Extract date from filename
                    filename = md_file.stem  # e.g., "2024-08-05"
                    entry_date = datetime.strptime(filename, "%Y-%m-%d").date()

                    # Load and re-index the entry
                    entry = self.load_entry(entry_date)
                    if entry:
                        self._update_database_index(entry)
                        count += 1

                except ValueError:
                    print(f"Skipping file with invalid date format: {md_file}")
                    continue
                except Exception as e:
                    print(f"Error processing file {md_file}: {e}")
                    continue

        except Exception as e:
            print(f"Error scanning existing files: {e}")

        return count

    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the SQLite database."""
        try:
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)

            # Simple file copy for SQLite backup
            import shutil

            shutil.copy2(self.db_path, backup_file)
            return True

        except Exception as e:
            print(f"Error creating database backup: {e}")
            return False

    def validate_vault(self) -> Dict[str, Any]:
        """Validate the vault structure and integrity."""
        issues = []

        # Check if required directories exist
        required_dirs = [self.vault_path, self.entries_path, self.metadata_path]
        for directory in required_dirs:
            if not directory.exists():
                issues.append(f"Missing directory: {directory}")

        # Check database integrity
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA integrity_check")
        except Exception as e:
            issues.append(f"Database integrity issue: {e}")

        # Check for orphaned files (files not in database)
        orphaned_files = []
        try:
            for md_file in self.entries_path.glob("*/*/*.md"):
                filename = md_file.stem
                try:
                    entry_date = datetime.strptime(filename, "%Y-%m-%d").date()
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.execute(
                            "SELECT 1 FROM entries WHERE date = ?",
                            (entry_date.isoformat(),),
                        )
                        if not cursor.fetchone():
                            orphaned_files.append(str(md_file))
                except ValueError:
                    orphaned_files.append(str(md_file))
        except Exception as e:
            issues.append(f"Error checking for orphaned files: {e}")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "orphaned_files": orphaned_files,
            "vault_path": str(self.vault_path),
            "entries_count": len(self.get_entry_dates()),
        }
