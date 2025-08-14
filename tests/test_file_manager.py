"""
Test suite for FileManager CRUD operations and vault management.
"""

import pytest
import tempfile
import sqlite3
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from dana_journal.storage.file_manager import FileManager, JournalEntry


class TestJournalEntry:
    """Test JournalEntry dataclass functionality."""

    def test_journal_entry_creation(self):
        """Test basic journal entry creation."""
        entry = JournalEntry(
            title="Test Entry",
            content="Test content here",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            date=date.today()
        )
        
        assert entry.title == "Test Entry"
        assert entry.content == "Test content here"
        assert entry.word_count == 3  # "Test content here"
        assert entry.tags == []  # Default empty list
        assert entry.version == 1
        
    def test_journal_entry_word_count(self):
        """Test word count calculation."""
        entry = JournalEntry(
            title="Test",
            content="This is a longer test content with multiple words",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            date=date.today()
        )
        
        # Actual word count: "This is a longer test content with multiple words" = 9 words
        assert entry.word_count == 9
        
    def test_journal_entry_empty_content(self):
        """Test journal entry with empty content."""
        entry = JournalEntry(
            title="Empty",
            content="",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            date=date.today()
        )
        
        assert entry.word_count == 0
        
    def test_journal_entry_with_tags(self):
        """Test journal entry with custom tags."""
        entry = JournalEntry(
            title="Tagged Entry",
            content="Content with tags",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            date=date.today(),
            tags=["work", "personal", "goals"]
        )
        
        assert len(entry.tags) == 3
        assert "work" in entry.tags


class TestFileManagerSetup:
    """Test FileManager initialization and setup."""

    def test_file_manager_initialization(self):
        """Test FileManager creates necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(temp_dir)
            
            assert fm.vault_path.exists()
            assert fm.entries_path.exists()
            assert fm.metadata_path.exists()
            assert fm.ai_cache_path.exists()
            assert fm.db_path.exists()
            
    def test_is_existing_vault_detection(self):
        """Test existing vault detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initially not a vault
            assert not FileManager.is_existing_vault(temp_dir)
            
            # Create a vault
            fm = FileManager(temp_dir)
            
            # Now should be detected as existing vault
            assert FileManager.is_existing_vault(temp_dir)
            
    def test_is_existing_vault_error_handling(self):
        """Test vault detection handles errors gracefully."""
        # Non-existent path should return False (path doesn't exist, so no vault)
        assert not FileManager.is_existing_vault("/non/existent/path")
        
    def test_database_initialization(self):
        """Test SQLite database is properly initialized."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fm = FileManager(temp_dir)
            
            # Check that tables exist
            with sqlite3.connect(fm.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='entries'"
                )
                result = cursor.fetchone()
                assert result is not None
                assert result[0] == "entries"


class TestFileManagerCRUD:
    """Test FileManager Create, Read, Update, Delete operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.fm = FileManager(self.temp_dir)
        self.test_date = date(2025, 8, 14)
        self.test_entry = JournalEntry(
            title="Test Entry",
            content="This is test content for the journal entry.",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            date=self.test_date,
            tags=["test", "unit-test"]
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_create_entry_basic(self):
        """Test creating a basic journal entry."""
        # Create entry using the method (title will be auto-generated)
        result = self.fm.create_entry(
            entry_date=self.test_date,
            content="Test content"
        )
        
        assert result is not None
        assert isinstance(result, JournalEntry)
        
        # Verify entry was created
        loaded_entry = self.fm.load_entry(self.test_date)
        assert loaded_entry is not None
        assert loaded_entry.title == "Aug 14, 2025"  # Auto-generated from date
        assert loaded_entry.content == "Test content"
        assert loaded_entry.date == self.test_date
        
    def test_create_entry_with_empty_content(self):
        """Test creating entry with empty content."""
        result = self.fm.create_entry(
            entry_date=self.test_date,
            content=""
        )
        
        assert result is not None
        assert isinstance(result, JournalEntry)
        
        loaded_entry = self.fm.load_entry(self.test_date)
        assert loaded_entry is not None
        assert loaded_entry.content == ""
        assert loaded_entry.title == "Aug 14, 2025"  # Auto-generated from date
        
    def test_load_non_existent_entry(self):
        """Test loading an entry that doesn't exist."""
        non_existent_date = date(1990, 1, 1)
        entry = self.fm.load_entry(non_existent_date)
        assert entry is None
        
    def test_save_entry(self):
        """Test saving a journal entry."""
        # Create and save entry
        result = self.fm.save_entry(self.test_entry)
        assert result is True
        
        # Load and verify
        loaded_entry = self.fm.load_entry(self.test_date)
        assert loaded_entry is not None
        assert loaded_entry.title == self.test_entry.title
        assert loaded_entry.content == self.test_entry.content
        assert loaded_entry.tags == self.test_entry.tags
        
    def test_update_existing_entry(self):
        """Test updating an existing journal entry."""
        # Create initial entry
        self.fm.create_entry(self.test_date, content="Original content")
        
        # Load, modify, and save
        entry = self.fm.load_entry(self.test_date)
        entry.content = "Updated content"
        # Note: keeping auto-generated title
        
        result = self.fm.save_entry(entry)
        assert result is True
        
        # Verify update
        updated_entry = self.fm.load_entry(self.test_date)
        assert updated_entry.content == "Updated content"
        assert updated_entry.title == "Aug 14, 2025"  # Still auto-generated from date
        
    def test_delete_entry(self):
        """Test deleting a journal entry."""
        # Create entry
        self.fm.create_entry(self.test_date, content="Content to delete")
        
        # Verify it exists
        assert self.fm.load_entry(self.test_date) is not None
        
        # Delete entry
        result = self.fm.delete_entry(self.test_date)
        assert result is True
        
        # Verify it's gone
        assert self.fm.load_entry(self.test_date) is None
        
    def test_delete_non_existent_entry(self):
        """Test deleting an entry that doesn't exist."""
        non_existent_date = date(1990, 1, 1)
        result = self.fm.delete_entry(non_existent_date)
        # FileManager returns True even for non-existent files (no-op is considered success)
        assert result is True
        
    def test_get_entry_dates(self):
        """Test retrieving all entry dates."""
        # Initially empty
        dates = self.fm.get_entry_dates()
        assert len(dates) == 0
        
        # Create multiple entries
        date1 = date(2025, 8, 1)
        date2 = date(2025, 8, 2)
        date3 = date(2025, 8, 3)
        
        self.fm.create_entry(date1, content="Content 1")
        self.fm.create_entry(date2, content="Content 2")
        self.fm.create_entry(date3, content="Content 3")
        
        dates = self.fm.get_entry_dates()
        assert len(dates) == 3
        assert date1 in dates
        assert date2 in dates
        assert date3 in dates


class TestFileManagerAdvanced:
    """Test FileManager advanced functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.fm = FileManager(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_ai_reflection_data(self):
        """Test saving and loading AI reflection data."""
        test_date = date(2025, 8, 14)
        ai_data = {
            "insights": ["Test insight 1", "Test insight 2"],
            "questions": ["Test question?"],
            "themes": ["reflection", "growth"],
            "generated_at": datetime.now().isoformat()
        }
        
        # Create entry with AI data
        entry = JournalEntry(
            title="AI Test",
            content="Content for AI analysis",
            created_at=datetime.now(),
            modified_at=datetime.now(),
            date=test_date,
            ai_reflection=ai_data
        )
        
        # Save and reload
        self.fm.save_entry(entry)
        loaded_entry = self.fm.load_entry(test_date)
        
        assert loaded_entry.ai_reflection is not None
        assert loaded_entry.ai_reflection["insights"] == ai_data["insights"]
        assert loaded_entry.ai_reflection["questions"] == ai_data["questions"]
        
    def test_search_entries(self):
        """Test searching through journal entries."""
        # Create test entries - they will have auto-generated date-based titles
        self.fm.create_entry(
            date(2025, 8, 1), 
            content="Today I went for a beautiful walk in the park"
        )
        self.fm.create_entry(
            date(2025, 8, 2), 
            content="Had an amazing coffee with friends"
        )
        self.fm.create_entry(
            date(2025, 8, 3), 
            content="Working on a challenging programming project"
        )
        
        # Search by month name (in title) - should find entry
        results = self.fm.search_entries("Aug 01")
        assert len(results) == 1
        assert "park" in results[0].content.lower()
        
        # Search by year (partial title match)
        results = self.fm.search_entries("2025")
        assert len(results) == 3  # All entries are from 2025
        
        # Search by month name (partial title match)  
        results = self.fm.search_entries("Aug")
        assert len(results) == 3  # All entries are from August
        
        # Search for non-existent term
        results = self.fm.search_entries("nonexistent")
        assert len(results) == 0
        
    def test_get_statistics(self):
        """Test getting vault statistics."""
        # Initially empty
        stats = self.fm.get_statistics()
        assert stats["total_entries"] == 0
        assert stats["total_words"] == 0
        
        # Add entries
        self.fm.create_entry(date(2025, 8, 1), content="Short entry")
        self.fm.create_entry(date(2025, 8, 2), content="This is a longer entry with more words")
        
        stats = self.fm.get_statistics()
        assert stats["total_entries"] == 2
        assert stats["total_words"] > 0
        
    def test_validate_vault(self):
        """Test vault validation functionality."""
        # Valid vault
        validation = self.fm.validate_vault()
        assert validation["is_valid"] is True
        assert len(validation.get("issues", [])) == 0
        
    def test_rename_entry(self):
        """Test renaming (moving) an entry to a different date."""
        old_date = date(2025, 8, 1)
        new_date = date(2025, 8, 15)
        
        # Create entry
        self.fm.create_entry(old_date, content="Content to move")
        
        # Rename entry
        result = self.fm.rename_entry(old_date, new_date)
        assert result is True
        
        # Verify old entry is gone and new entry exists
        assert self.fm.load_entry(old_date) is None
        new_entry = self.fm.load_entry(new_date)
        assert new_entry is not None
        assert new_entry.content == "Content to move"
        assert new_entry.title == "Aug 15, 2025"  # Auto-generated title for new date


class TestFileManagerFileSystem:
    """Test FileManager file system operations and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.fm = FileManager(self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_file_path_generation(self):
        """Test correct file path generation for entries."""
        test_date = date(2025, 8, 14)
        expected_path = self.fm.entries_path / "2025" / "08" / "2025-08-14.md"
        actual_path = self.fm._get_entry_file_path(test_date)
        
        assert actual_path == expected_path
        
    def test_frontmatter_parsing(self):
        """Test YAML frontmatter parsing and creation."""
        test_content = """---
title: Test Title
created_at: 2025-08-14T10:00:00
modified_at: 2025-08-14T10:00:00
tags:
  - test
  - parsing
word_count: 5
---

This is test content."""

        frontmatter, content = self.fm._parse_frontmatter(test_content)
        
        assert frontmatter["title"] == "Test Title"
        assert "test" in frontmatter["tags"]
        assert frontmatter["word_count"] == 5
        assert content.strip() == "This is test content."
        
    def test_content_hash(self):
        """Test content hash generation for change detection."""
        content1 = "This is test content"
        content2 = "This is test content"
        content3 = "This is different content"
        
        hash1 = self.fm._content_hash(content1)
        hash2 = self.fm._content_hash(content2)
        hash3 = self.fm._content_hash(content3)
        
        assert hash1 == hash2  # Same content, same hash
        assert hash1 != hash3  # Different content, different hash
        
    def test_scan_existing_files(self):
        """Test scanning and indexing existing files."""
        # Create some files directly in the filesystem
        test_date = date(2025, 8, 14)
        file_path = self.fm._get_entry_file_path(test_date)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write("---\ntitle: 'Aug 14, 2025'\ncreated_at: '2025-08-14T10:00:00'\nmodified_at: '2025-08-14T10:00:00'\ndate: '2025-08-14'\nword_count: 6\n---\nContent written directly to file")
        
        # Scan and index
        count = self.fm.scan_existing_files()
        assert count == 1
        
        # Verify it can be loaded through FileManager
        entry = self.fm.load_entry(test_date)
        assert entry is not None
        assert entry.title == "Aug 14, 2025"  # Should match our file's frontmatter


if __name__ == "__main__":
    pytest.main([__file__])