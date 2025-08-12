# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is DANA - safe journal space, a privacy-first desktop journaling application built with Python and Flet with a warm, companion-like interface. The app provides local AI-powered insights through collapsible wisdom cards while keeping all user data on their device.

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
│       ├── onboarding.py      # 4-step onboarding flow with AI setup
│       ├── calendar.py        # Interactive calendar with entry indicators
│       ├── text_editor.py     # Enhanced markdown text editor
│       ├── file_explorer.py   # File navigation component
│       └── ai_reflection.py   # Dana's collapsible wisdom component
├── storage/
│   ├── file_manager.py        # Complete file I/O with SQLite indexing
│   ├── auto_save.py           # Auto-save functionality
│   └── integration.py         # Storage integration layer
└── ai/
    ├── __init__.py            # AI module initialization
    ├── download_model.py      # AI model download manager
    └── prompts.py             # Complete prompt engineering system
```

### Key Components

**JournalVaultApp (main.py)**: Central application class managing page state, UI components, and user interactions. Uses Obsidian-inspired layout with left sidebar containing calendar and file explorer.

**Theme System (ui/theme.py)**: Dark-mode only theme with consistent color palette. Provides `ThemedContainer`, `ThemedText`, and `ThemedCard` components for consistent styling.

**Onboarding Flow (ui/components/onboarding.py)**: Enhanced 4-step process:
1. Welcome and feature overview
2. Privacy explanation 
3. **Dual-mode vault setup** with radio button selection:
   - Create New Vault: Name + parent directory selection
   - Load Existing Vault: Smart detection of existing vault structures
   - Real-time path preview and validation
   - Context-aware completion buttons
4. **AI Setup**: Optional Qwen2.5-3B-Instruct model download with progress tracking

**Calendar Component (ui/components/calendar.py)**: Interactive month navigation with entry indicators, date selection, and "Today" button. Integrates with journal entry system.

**Dana's Wisdom Component (ui/components/ai_reflection.py)**: Collapsible companion wisdom component for displaying AI-generated insights, questions, and themes with enhanced regeneration UX, smooth animations, and persistent display.

**File Manager (storage/file_manager.py)**: Complete file management system with SQLite indexing, YAML frontmatter parsing, entry CRUD operations, search capabilities, and vault validation.

**AI Download Manager (ai/download_model.py)**: Handles downloading and managing the Qwen2.5-3B-Instruct model with progress tracking, system requirements checking, and file validation.

**Configuration (config/app_config.py)**: Persistent settings stored in `~/.journal_vault/config.json` including onboarding status, storage path, window state, and AI configuration.

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
- **Main Content Area**: Journal text editor with entry management
- **Inline AI Section**: AI reflection component displayed below text editor
- **Color Scheme**: Dark mode with violet/indigo accents (#8B5CF6 primary)
- **Interactive Elements**: Delete confirmation dialogs, progress indicators, file pickers

## Development Status

### Implemented ✅
- Complete Flet-based application structure with DANA companion interface
- Dark theme system with reusable components and sage green accents
- Interactive calendar with navigation and entry indicators
- **Enhanced 4-step onboarding** with dual-mode vault setup and AI configuration
- **Smart vault detection** for existing journal folders
- **Real-time path preview** with proper macOS folder selection
- Configuration persistence system with vault metadata
- **Complete file manager with SQLite indexing** for fast entry lookup
- **Collapsible wisdom cards** with enhanced regeneration UX and smooth animations
- **Complete AI prompt engineering system** with Melanie Klein persona
- **AI model download manager** with progress tracking and validation
- **Enhanced markdown text editor** with formatting toolbar
- **Auto-save functionality** with configurable delay
- **Complete CRUD operations** for journal entries
- **Entry search and filtering** capabilities
- **Vault validation and integrity checking**
- **Delete confirmation UI** with platform-appropriate dialogs
- Comprehensive error handling and user feedback with companion-like messaging

### In Progress 🔄
- **AI inference integration** - Complete infrastructure ready, inference pipeline pending (99% complete)
- **Cross-platform packaging** for distribution
- **Advanced search features** with full-text indexing
- **Data export/import** functionality

### Planned ❌
- **Enhanced AI features**: Multi-entry theme analysis, mood pattern tracking
- **Plugin system** for extensibility
- **Sync capabilities** for backup and sharing
- **Rich text editor** with WYSIWYG features
- **Data visualization** of writing patterns and trends
- **Mobile companion app** integration
- **Advanced wisdom features**: Personalized insights, growth tracking

## Important Implementation Details

### Dependencies
Uses focused dependencies managed by `uv` (requires Python 3.11+):
- `flet[all]==0.28.3` - Cross-platform UI framework
- `pydantic>=2.8.0` - Data validation and settings
- `python-dateutil>=2.9.0` - Date handling utilities
- `pyyaml>=6.0.2` - YAML parsing for frontmatter
- `llama-cpp-python>=0.2.90` - Local AI model inference
- `huggingface-hub>=0.25.0` - AI model downloads
- `psutil>=5.9.0` - System resource monitoring
- `requests>=2.31.0` - HTTP requests for model downloading

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