# Dana Desktop

A privacy-first journaling application for macOS, Windows, and Linux. Built with Python and Flet. All data and AI processing happen entirely on your device.

![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-macOS%20|%20Windows%20|%20Linux-green.svg)

---

## Features

### Available now
- **100% local operation** — no internet required after setup, no telemetry
- **Interactive calendar** — month navigation with entry indicators and date selection
- **Markdown editor** — formatting toolbar, auto-save (30s default)
- **Smart vault management** — create a new vault or load an existing journal folder
- **Dana's Wisdom** — collapsible AI insight cards powered by local Qwen2.5-3B inference
- **SQLite indexing** — fast entry lookup, search, and filtering
- **Cross-platform builds** — macOS .app, Windows .exe, Linux binary, PWA

### Coming soon
- Advanced full-text search across all entries
- Mood and theme pattern tracking
- PDF/HTML export
- Data sync for backup

---

## Quick start

### Option 1: Pre-built package

Download the latest release for your platform from GitHub Releases:

- **macOS**: `dana-journal.app` — drag to Applications
- **Windows**: `dana-journal.exe` installer
- **Linux**: `dana-journal` binary — `chmod +x` then run

### Option 2: From source

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/your-username/journal-vault.git
cd journal-vault/dana-desktop

# Install dependencies
uv sync

# Run the app
uv run python src/main.py
```

---

## Onboarding

First launch guides you through four steps:

1. **Welcome** — feature overview and privacy principles
2. **Privacy** — what "local-only" means in practice
3. **Vault setup** — choose between:
   - *Create New Vault*: pick a parent directory, name your vault
   - *Load Existing Vault*: smart detection of existing journal folders
4. **AI Setup** — optional download of the Qwen2.5-3B-Instruct model (~2GB)

To reset onboarding during development:
```bash
uv run python tests/reset_onboarding.py
uv run python src/main.py
```

---

## Development

### Daily workflow

```bash
# Install all dependencies (including dev)
uv sync

# Run the application
uv run python src/main.py

# Run tests
uv run pytest

# Format code
uv run black .

# Lint
uv run ruff check .
```

### Project structure

```
dana-desktop/
├── pyproject.toml       Project config and dependencies (uv)
├── src/
│   ├── main.py          JournalVaultApp — central state and UI orchestration
│   ├── assets/          App icons (Flet auto-detects from assets/)
│   ├── config/
│   │   └── app_config.py  Persistent settings in ~/.dana_journal/config.json
│   ├── ui/
│   │   ├── theme.py        Dana theme system (ThemedContainer, ThemedText, ThemedCard)
│   │   └── components/
│   │       ├── onboarding.py      4-step setup wizard
│   │       ├── calendar.py        Interactive calendar with entry indicators
│   │       ├── text_editor.py     Markdown editor with formatting toolbar
│   │       ├── file_explorer.py   Vault file navigation
│   │       └── ai_reflection.py   Collapsible wisdom cards
│   ├── storage/
│   │   ├── file_manager.py   CRUD + SQLite indexing + YAML frontmatter parsing
│   │   ├── auto_save.py      Debounced auto-save
│   │   └── integration.py    Storage integration layer
│   └── ai/
│       ├── download_model.py  HuggingFace model download with progress tracking
│       ├── inference.py       Thread-safe local inference (llama-cpp-python)
│       ├── service.py         AI pipeline orchestration + caching
│       └── prompts.py         Prompt engineering (Melanie Klein companion persona)
├── tests/               pytest test suite
├── scripts/
│   ├── build.sh         Cross-platform build script
│   ├── package.sh       Release packaging
│   └── version.py       Semantic version management
└── docs/
    ├── ARCHITECTURE.md  Technical deep-dive
    ├── PACKAGING.md     Distribution guide
    └── PROJECT_OUTLINE.md  Roadmap and status
```

### Key component notes

**`src/main.py` — JournalVaultApp**: Central class managing all page state. Obsidian-inspired layout: left sidebar (calendar + file explorer) and main content area (editor + wisdom cards).

**`src/ui/theme.py`**: Terracotta `#E07A5F` primary, sage green `#81B29A` accents, warm cream surfaces. Provides `ThemedContainer`, `ThemedText`, `ThemedCard`.

**`src/ai/inference.py`**: Thread-safe, async-compatible llama-cpp-python wrapper. Handles model loading, memory management, and health monitoring.

**`src/storage/file_manager.py`**: SQLite-backed entry index for fast lookup. All I/O uses YAML frontmatter + markdown format.

---

## Build and packaging

```bash
# Development build for current platform
./scripts/build.sh dev

# Production builds
./scripts/build.sh macos      # macOS .app bundle
./scripts/build.sh windows    # Windows .exe
./scripts/build.sh linux      # Linux binary
./scripts/build.sh web        # Progressive Web App
./scripts/build.sh all        # All platforms

# Clean build artifacts
./scripts/build.sh clean
```

### Version management

```bash
python scripts/version.py current           # Show current and next versions
python scripts/version.py bump patch        # 0.1.0 → 0.1.1
python scripts/version.py bump minor        # 0.1.0 → 0.2.0
python scripts/version.py release minor     # Bump + git tag
```

### Release workflow

```bash
./scripts/package.sh release-patch      # Bump patch, build all, tag
./scripts/package.sh build-all          # Build all platforms
./scripts/package.sh check-health       # Validate build environment
./scripts/package.sh generate-checksums # SHA256 checksums for distribution
```

### Platform build requirements

| Platform | Requirements |
|----------|-------------|
| All | Python 3.11+, uv, Git |
| macOS | Xcode CLI tools (`xcode-select --install`), CocoaPods |
| Windows | Visual Studio Build Tools (C++), Windows 10 SDK |
| Linux | `build-essential`, `libgtk-3-dev` |

---

## Data format

### Storage layout

```
Your Journal Directory/
├── .dana_journal/
│   ├── config.json     App settings (onboarding state, AI config, window position)
│   ├── index.sqlite    Fast entry lookup index
│   └── ai_cache/       AI reflection cache
└── entries/
    └── YYYY/MM/
        └── YYYY-MM-DD.md
```

### Entry file format

```yaml
---
title: "Journal Entry - January 15, 2025"
created_at: "2025-01-15T09:30:00"
modified_at: "2025-01-15T10:15:00"
tags: ["reflection", "goals"]
word_count: 247
mood_rating: 8
version: 1
---

# Morning Reflections

Your content in **markdown format**.
```

### Configuration (`~/.dana_journal/config.json`)

```json
{
  "onboarded": true,
  "storage_path": "/Users/you/Documents/My Journal",
  "vault_name": "My Vault",
  "window_state": { "width": 1400, "height": 900, "maximized": false },
  "ai_enabled": true,
  "ai_model_downloaded": true,
  "ai_model_path": "...",
  "ai_inference_settings": {}
}
```

---

## Privacy

- **No network calls during use** — after the optional one-time model download
- **Standard file format** — plain markdown you can open in any editor
- **No telemetry** — no usage tracking, no crash reporting
- **Portable** — backup or version-control your journal folder directly

---

## Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific files
uv run pytest tests/test_file_manager.py
uv run pytest tests/test_ai_service.py

# Manual component tests
uv run python tests/test_folder_selection.py
uv run python tests/test_file_picker.py

# Fresh state for testing
rm -rf ~/.dana_journal
uv run python tests/reset_onboarding.py
```

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes following existing patterns
4. Run quality checks: `uv run pytest && uv run black . && uv run ruff check .`
5. Commit and open a PR

**Code style:** Black (88-char lines), Ruff linting, type hints where practical.
