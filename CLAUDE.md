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

# Reset onboarding for testing (development utility)
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
│   ├── theme.py         # Dana theme system with ThemedContainer/ThemedText components
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
    ├── inference.py           # Local AI inference engine with llama-cpp-python
    ├── service.py             # AI reflection service orchestration
    └── prompts.py             # Complete prompt engineering system

# Note: Assets are located in the project root
assets/
└── icons/                     # Application icons and branding assets
    ├── dana_logo.svg          # Main Dana logo
    └── dana_icon_*.png        # App icons in multiple sizes
```

### Key Components

**JournalVaultApp (main.py)**: Central application class managing page state, UI components, and user interactions. Uses Obsidian-inspired layout with left sidebar containing calendar and file explorer.

**Theme System (ui/theme.py)**: Dana theme system with warm, companion-like color palette featuring terracotta primary (#E07A5F), sage green accents (#81B29A), and warm cream surfaces. Provides `ThemedContainer`, `ThemedText`, and `ThemedCard` components for consistent styling.

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

**AI Inference Engine (ai/inference.py)**: Local AI inference using llama-cpp-python with thread-safe, async-compatible generation, memory management, and model health monitoring.

**AI Reflection Service (ai/service.py)**: Orchestrates the complete AI pipeline, combining inference, prompt engineering, and caching to provide journal reflection capabilities with warm, companion-like insights.

**Configuration (config/app_config.py)**: Persistent settings stored in `~/.journal_vault/config.json` including onboarding status, storage path, window state, and AI configuration.

### Data Storage Format

Journal entries are stored as markdown files with YAML frontmatter:
```
User's Journal Directory/
├── .journal_vault/
│   ├── config.json          # App settings
│   ├── index.sqlite         # Entry indexing database
│   └── ai_cache/            # AI reflection cache
└── entries/
    └── YYYY/MM/
        └── YYYY-MM-DD.md    # Journal entry with metadata
```

### UI Layout Philosophy

The application follows an Obsidian-inspired design:
- **Left Sidebar**: Calendar component and file explorer
- **Main Content Area**: Journal text editor with entry management
- **Inline AI Section**: AI reflection component displayed below text editor
- **Color Scheme**: Dana theme with terracotta primary (#E07A5F), sage green accents (#81B29A), and warm cream surfaces
- **Typography**: Dual-font system using Inter for UI elements and Crimson Pro for journal content
- **Interactive Elements**: Delete confirmation dialogs, progress indicators, file pickers

## Development Status

### Implemented ✅
- Complete Flet-based application structure with DANA companion interface
- **Dana theme system** with warm, companion-like color palette and dual typography
- Interactive calendar with navigation and entry indicators
- **Enhanced 4-step onboarding** with dual-mode vault setup and AI configuration
- **Smart vault detection** for existing journal folders
- **Real-time path preview** with proper macOS folder selection
- Configuration persistence system with vault metadata
- **Complete file manager with SQLite indexing** for fast entry lookup
- **Collapsible wisdom cards** with enhanced regeneration UX and smooth animations
- **Complete AI prompt engineering system** with Melanie Klein persona
- **AI model download manager** with progress tracking and validation
- **Local AI inference engine** with llama-cpp-python integration
- **AI reflection service** orchestrating complete AI pipeline
- **Enhanced markdown text editor** with formatting toolbar
- **Auto-save functionality** with configurable delay
- **Complete CRUD operations** for journal entries
- **Entry search and filtering** capabilities
- **Vault validation and integrity checking**
- **Delete confirmation UI** with platform-appropriate dialogs
- **Dana branding integration** with custom app icons and assets
- Comprehensive error handling and user feedback with companion-like messaging

### In Progress 🔄
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
- **Export functionality**: PDF, HTML, and other format exports
- **Advanced search**: Full-text search with semantic similarity

## Important Implementation Details

### Dependencies
Uses focused dependencies managed by `uv` (requires Python 3.11+):

**Production Dependencies:**
- `flet[all]==0.28.3` - Cross-platform UI framework
- `pydantic>=2.8.0` - Data validation and settings
- `python-dateutil>=2.9.0` - Date handling utilities
- `pyyaml>=6.0.2` - YAML parsing for frontmatter
- `llama-cpp-python>=0.2.90` - Local AI model inference
- `huggingface-hub>=0.25.0` - AI model downloads
- `psutil>=5.9.0` - System resource monitoring
- `requests>=2.31.0` - HTTP requests for model downloading

**Development Dependencies:**
- `pytest>=8.4.1` - Testing framework
- `pytest-asyncio>=1.1.0` - Async testing support
- `black>=25.1.0` - Code formatting
- `ruff>=0.12.7` - Fast Python linter

### Configuration Management
Settings are automatically persisted to `~/.journal_vault/config.json`. Key settings include:
- `onboarded`: Boolean tracking completion of setup
- `storage_path`: User-selected journal storage directory
- `vault_name`: User-defined vault name
- `window_state`: Size and position persistence
- `ai_enabled`: AI features activation status
- `ai_model_downloaded`: Model download completion status
- `ai_model_path`: Path to downloaded AI model
- `ai_inference_settings`: AI configuration and preferences

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

### Key Implementation Highlights
- **Complete AI Infrastructure**: Local inference pipeline with Qwen2.5-3B-Instruct model
- **Companion Interface**: Warm, supportive language throughout the application
- **Dana Branding**: Custom app icons and consistent visual identity
- **Privacy-First**: All processing happens locally with no external dependencies
- **Professional Architecture**: Clean separation of concerns with modular design
- **Performance Optimized**: SQLite indexing, debounced auto-save, efficient file operations

### Testing
- All test files should be stored in the `/tests` folder
- Use `pytest` as the primary testing framework
- Async testing supported through `pytest-asyncio`