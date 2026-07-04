# CLAUDE.md — Dana Desktop

This file provides guidance to Claude Code when working in `dana-desktop/`.

## Project Overview

Dana Desktop is a privacy-first journaling application built with Python 3.11+ and Flet. It provides local AI-powered insights through collapsible wisdom cards while keeping all user data on the device.

The app follows Flet's standard layout: all modules live in `src/` with absolute imports. `pyproject.toml` configures `[tool.flet.app] path = "src"`.

## Development Commands

### Running the Application
```bash
uv run python src/main.py
```

### Development Setup
```bash
uv sync           # Install all dependencies including dev
uv sync --no-dev  # Production dependencies only
```

### Testing and Code Quality
```bash
uv run pytest
uv run pytest -v
uv run black .
uv run ruff check .

# Specific test files
uv run python tests/test_file_picker.py
uv run python tests/test_folder_selection.py

# Reset onboarding for testing
uv run python tests/reset_onboarding.py
```

### Packaging and Distribution
```bash
./scripts/build.sh dev        # Current platform dev build
./scripts/build.sh macos      # macOS .app bundle
./scripts/build.sh windows    # Windows .exe
./scripts/build.sh linux      # Linux binary
./scripts/build.sh web        # PWA
./scripts/build.sh all        # All platforms
./scripts/build.sh clean      # Clean artifacts

python scripts/version.py current
python scripts/version.py bump patch
python scripts/version.py release minor

./scripts/package.sh release-patch
./scripts/package.sh build-all
./scripts/package.sh check-health
```

## Project Architecture

### Core Structure
```
src/
├── main.py              # JournalVaultApp — central state and UI orchestration
├── assets/              # Icons (auto-detected by Flet from assets/)
├── config/
│   └── app_config.py    # Persistent settings in ~/.dana_journal/config.json
├── ui/
│   ├── theme.py         # Dana theme: ThemedContainer, ThemedText, ThemedCard
│   └── components/
│       ├── onboarding.py      # 4-step setup wizard
│       ├── calendar.py        # Interactive calendar with entry indicators
│       ├── text_editor.py     # Markdown editor with formatting toolbar
│       ├── file_explorer.py   # Vault file navigation
│       └── ai_reflection.py   # Collapsible wisdom cards
├── storage/
│   ├── file_manager.py        # CRUD + SQLite indexing + YAML frontmatter
│   ├── auto_save.py           # Debounced auto-save
│   └── integration.py         # Storage integration layer
└── ai/
    ├── __init__.py
    ├── download_model.py      # HuggingFace model download + validation
    ├── inference.py           # Thread-safe llama-cpp-python inference engine
    ├── service.py             # AI pipeline orchestration + caching
    └── prompts.py             # Prompt engineering (Melanie Klein persona)
```

### Key Components

**JournalVaultApp (`src/main.py`)**: Central class managing all page state, component lifecycle, and user interactions. Obsidian-inspired layout — left sidebar (calendar + file explorer), main area (editor + wisdom cards).

**Theme System (`src/ui/theme.py`)**: Terracotta `#E07A5F` primary, sage green `#81B29A` accents. `ThemedContainer`, `ThemedText`, `ThemedCard` for consistent styling.

**Onboarding (`src/ui/components/onboarding.py`)**: 4-step flow:
1. Welcome
2. Privacy explanation
3. Dual-mode vault setup (Create New / Load Existing) with real-time path preview
4. Optional Qwen2.5-3B-Instruct model download with progress tracking

**File Manager (`src/storage/file_manager.py`)**: SQLite-backed entry index, YAML frontmatter parsing, full CRUD, search, vault validation.

**AI Inference (`src/ai/inference.py`)**: Thread-safe async llama-cpp-python wrapper. Manages model loading, memory, health monitoring.

**AI Service (`src/ai/service.py`)**: Orchestrates inference + prompt engineering + caching.

**Config (`src/config/app_config.py`)**: Persists to `~/.dana_journal/config.json`. Keys: `onboarded`, `storage_path`, `vault_name`, `window_state`, `ai_enabled`, `ai_model_downloaded`, `ai_model_path`, `ai_inference_settings`.

### Data Storage Format

```
User's Journal Directory/
├── .dana_journal/
│   ├── config.json     App settings
│   ├── index.sqlite    Entry index
│   └── ai_cache/       AI reflection cache
└── entries/
    └── YYYY/MM/
        └── YYYY-MM-DD.md
```

### UI Layout
- Left sidebar: calendar + file explorer
- Main area: markdown editor + wisdom cards below
- Color scheme: terracotta `#E07A5F`, sage green `#81B29A`, warm cream surfaces
- Typography: Inter (UI), Crimson Pro (journal content)

## Development Status

### Implemented
- Flet app with DANA companion interface
- Theme system with dual typography
- 4-step onboarding with dual vault setup
- Smart vault detection + real-time path preview
- Complete file manager with SQLite indexing
- Collapsible wisdom cards with smooth animations
- Full AI prompt engineering (Melanie Klein persona)
- Model download manager with progress and validation
- Local AI inference engine (llama-cpp-python)
- Markdown editor with formatting toolbar and auto-save
- Full CRUD, search, filtering
- Vault validation and integrity checking
- Dana branding (custom icons, consistent palette)

### In Progress
- Cross-platform packaging for distribution
- Advanced full-text search
- Data export/import

### Planned
- Multi-entry theme analysis, mood tracking
- Rich text WYSIWYG editor
- Data visualization
- Sync for backup
- PDF/HTML export
- Mobile companion app

## Dependencies

**Production:** `flet[all]==0.28.3`, `pydantic>=2.8.0`, `python-dateutil>=2.9.0`, `pyyaml>=6.0.2`, `llama-cpp-python>=0.2.90`, `huggingface-hub>=0.25.0`, `psutil>=5.9.0`, `requests>=2.31.0`

**Dev:** `pytest>=8.4.1`, `pytest-asyncio>=1.1.0`, `black>=25.1.0`, `ruff>=0.12.7`

## Conventions
- All UI components inherit from themed base classes
- Import style: `from ui.components import ComponentName` (absolute, Flet-compliant)
- Storage operations use async patterns for UI responsiveness
- Error handling uses companion-like language throughout
- All test files go in `tests/`; use pytest with pytest-asyncio for async tests
