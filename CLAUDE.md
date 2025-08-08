# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is AI Journal Vault, a privacy-first desktop journaling application built with Python and Flet. The app provides local AI-powered insights while keeping all user data on their device.

## Development Commands

### Running the Application
```bash
uv run python -m journal_vault.main
```

### Development Setup
```bash
# Install dependencies (including dev dependencies)
uv sync

# Install only production dependencies
uv sync --no-dev
```

### Testing and Code Quality
```bash
# Run tests
uv run pytest

# Format code with Black
uv run black .

# Lint code with Ruff
uv run ruff check .

# Run specific test files
uv run python tests/test_file_picker.py
uv run python tests/test_folder_selection.py

# Reset onboarding for testing
uv run python tests/reset_onboarding.py
```

## Project Architecture

### Core Structure
```
src/journal_vault/
├── main.py              # Main application entry point with JournalVaultApp class
├── config/
│   └── app_config.py    # Configuration management and persistence
├── ui/
│   ├── theme.py         # Dark theme system with ThemedContainer/ThemedText components
│   └── components/      # Reusable UI components
│       ├── onboarding.py    # 3-step onboarding flow with native folder picker
│       ├── calendar.py      # Interactive calendar with entry indicators
│       ├── text_editor.py   # Enhanced markdown text editor
│       └── file_explorer.py # File navigation component
├── storage/
│   ├── file_manager.py      # File I/O operations for journal entries
│   ├── auto_save.py         # Auto-save functionality
│   └── integration.py       # Storage integration layer
└── ai/                      # AI integration modules (planned)
```

### Key Components

**JournalVaultApp (main.py)**: Central application class managing page state, UI components, and user interactions. Uses Obsidian-inspired layout with left sidebar containing calendar and file explorer.

**Theme System (ui/theme.py)**: Dark-mode only theme with consistent color palette. Provides `ThemedContainer`, `ThemedText`, and `ThemedCard` components for consistent styling.

**Onboarding Flow (ui/components/onboarding.py)**: Enhanced 3-step process:
1. Welcome and feature overview
2. Privacy explanation 
3. **Dual-mode vault setup** with radio button selection:
   - Create New Vault: Name + parent directory selection
   - Load Existing Vault: Smart detection of existing vault structures
   - Real-time path preview and validation
   - Context-aware completion buttons

**Calendar Component (ui/components/calendar.py)**: Interactive month navigation with entry indicators, date selection, and "Today" button. Integrates with journal entry system.

**Configuration (config/app_config.py)**: Persistent settings stored in `~/.journal_vault/config.json` including onboarding status, storage path, and window state.

### Data Storage Format

Journal entries are stored as markdown files with YAML frontmatter:
```
User's Journal Directory/
├── .journal_vault/
│   ├── config.json          # App settings
│   ├── index.sqlite         # Entry indexing (planned)
│   └── ai_cache/            # AI reflection cache (planned)
└── entries/
    └── YYYY/MM/
        └── YYYY-MM-DD.md    # Journal entry with metadata
```

### UI Layout Philosophy

The application follows an Obsidian-inspired design:
- **Left Sidebar**: Calendar component and file explorer
- **Main Content Area**: Journal text editor
- **Bottom Panel**: AI reflection area (planned)
- **Color Scheme**: Dark mode with violet/indigo accents (#8B5CF6 primary)

## Development Status

### Implemented ✅
- Complete Flet-based application structure
- Dark theme system with reusable components  
- Interactive calendar with navigation and entry indicators
- **Enhanced 3-step onboarding** with dual-mode vault setup
- **Smart vault detection** for existing journal folders
- **Real-time path preview** with proper macOS folder selection
- Configuration persistence system with vault metadata
- Comprehensive error handling and user feedback

### In Progress 🔄
- File manager and storage system (`storage/` modules)
- Enhanced markdown editor with formatting
- Auto-save functionality
- Real entry loading/saving

### Planned ❌
- AI integration with Qwen2.5-3B-Instruct model
- Reflection generation and caching
- SQLite indexing for fast entry lookup
- Cross-platform packaging

## Important Implementation Details

### Dependencies
Uses minimal, focused dependencies managed by `uv`:
- `flet>=0.24.1` - Cross-platform UI framework
- `pydantic>=2.8.0` - Data validation and settings
- `python-dateutil>=2.9.0` - Date handling utilities

### Configuration Management
Settings are automatically persisted to `~/.journal_vault/config.json`. Key settings include:
- `onboarded`: Boolean tracking completion of setup
- `storage_path`: User-selected journal storage directory
- `window_state`: Size and position persistence

### File Structure Conventions
- All UI components inherit from themed base classes
- Import structure: `from .ui.components import ComponentName`
- Storage operations use async patterns for UI responsiveness
- Error handling with user-friendly messages throughout

### Testing Approach
- Utility scripts in `tests/` for development workflow
- Component-level testing for UI elements
- Integration testing for storage operations
- Use `pytest` as the test framework with async support

This codebase prioritizes user privacy, clean architecture, and rapid development cycles while maintaining code quality through consistent patterns and comprehensive testing.
- for all test generated, store it in /tests folder