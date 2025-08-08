# AI Journal Vault

A privacy-first desktop journaling application with local AI-powered insights. Write, reflect, and discover patterns in your thoughts while keeping all data on your device.

![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-macOS%20|%20Windows%20|%20Linux-green.svg)

## 🌟 Features

### Core Functionality (Available Now)
- **Privacy-First Design**: 100% local operation - all your data stays on your device
- **Interactive Calendar**: Visual month navigation with entry indicators and date selection
- **Markdown Editor**: Rich text editing with auto-save functionality
- **Smart Organization**: Automatic file organization by date (YYYY/MM/DD structure)
- **Dual-Mode Setup**: Create new vaults or load existing journal folders
- **Dark Theme**: Obsidian-inspired interface optimized for focused writing

### Coming Soon
- **Pattern Recognition**: Discover themes and insights in your writing
- **Advanced Search**: Full-text search across all entries
- **Enhanced Editor**: Advanced markdown features and formatting tools

## 🚀 Quick Start

### Prerequisites

- **Python 3.11 or higher**
- **uv package manager** (recommended for dependency management)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/journal-vault.git
   cd journal-vault
   ```

2. **Install dependencies:**
   ```bash
   # Install uv if you don't have it
   pip install uv
   
   # Install project dependencies
   uv sync
   ```

### Running the Application

#### First Time Setup (with onboarding)
```bash
uv run python -m journal_vault.main
```

This will guide you through the 3-step onboarding process:
1. **Welcome**: Learn about features and privacy principles
2. **Privacy**: Understand local-only data processing
3. **Storage**: Choose between creating a new vault or loading an existing one

#### Reset Onboarding (for testing)
```bash
# Reset the onboarding state
uv run python tests/reset_onboarding.py

# Then run the app
uv run python -m journal_vault.main
```

#### Skip Onboarding (after first setup)
Once you've completed onboarding, simply run:
```bash
uv run python -m journal_vault.main
```

The app will remember your settings and open directly to the main interface.

## 🏗️ Development

### Project Structure

```
src/journal_vault/
├── main.py              # Main application entry point
├── config/
│   └── app_config.py    # Configuration management
├── ui/
│   ├── theme.py         # Dark theme system
│   └── components/      # Reusable UI components
│       ├── onboarding.py    # 3-step setup wizard
│       ├── calendar.py      # Interactive calendar
│       ├── text_editor.py   # Markdown text editor
│       └── file_explorer.py # File navigation
├── storage/             # File management system
└── ai/                  # AI integration (planned)
```

### Development Commands

```bash
# Install development dependencies
uv sync

# Run the application
uv run python -m journal_vault.main

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code  
uv run ruff check .

# Reset onboarding for testing
uv run python tests/reset_onboarding.py
```

### Data Storage Format

Journal entries are stored as markdown files with YAML frontmatter:

```
Your Journal Directory/
├── .journal_vault/
│   ├── config.json          # App settings
│   ├── index.sqlite         # Entry indexing (planned)
│   └── ai_cache/            # AI reflection cache (planned)
└── entries/
    └── YYYY/MM/
        └── YYYY-MM-DD.md    # Daily journal entries
```

#### Entry File Format

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

Your journal content goes here in **markdown format**.

## Today's Goals
- [ ] Complete project documentation
- [x] Morning meditation
- [ ] Evening walk
```

## 🔧 Configuration

### App Settings

Configuration is automatically managed in `~/.journal_vault/config.json`:

```json
{
  "onboarded": true,
  "storage_path": "/Users/username/Documents/My Journal",
  "window_state": {
    "width": 1400,
    "height": 900,
    "maximized": false
  },
  "preferences": {
    "auto_save_interval": 30,
    "show_word_count": true
  }
}
```

### Vault Types

The application supports two vault setup modes:

#### Create New Vault
- Choose a parent directory and vault name
- Creates a new folder structure with `.journal_vault/` metadata
- Perfect for starting fresh

#### Load Existing Vault
- Smart detection of existing journal structures
- Supports both confirmed vaults (with `.journal_vault/`) and compatible folders
- Automatically initializes metadata for compatible structures

## 🛡️ Privacy & Security

- **100% Local Processing**: No internet connection required after installation
- **Your Data, Your Control**: All files stored in standard markdown format
- **Transparent Storage**: Human-readable files you can backup, version control, or migrate
- **No Telemetry**: No usage tracking or data collection

## 🧪 Testing

### Manual Testing

```bash
# Test folder selection components
uv run python tests/test_folder_selection.py

# Test file picker functionality  
uv run python tests/test_file_picker.py

# Reset onboarding state
uv run python tests/reset_onboarding.py
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test files
uv run pytest tests/test_specific.py

# Run with verbose output
uv run pytest -v
```

## 🎨 UI Design

The application features an Obsidian-inspired dark theme with:

- **Left Sidebar**: Calendar and file explorer
- **Main Area**: Markdown text editor  
- **Color Scheme**: Deep midnight backgrounds with violet accents (#8B5CF6)
- **Typography**: Clean, readable fonts with proper hierarchy
- **Responsive Layout**: Adapts to different window sizes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the existing code style
4. Run tests and formatting (`uv run pytest && uv run black . && uv run ruff check .`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Use **Black** for code formatting
- Use **Ruff** for linting  
- Follow existing import patterns
- Add type hints where possible
- Write descriptive commit messages

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: Check the `documentation/` folder for detailed guides
- **Issues**: Report bugs or request features via GitHub Issues
- **Architecture**: See `documentation/ARCHITECTURE.md` for technical details
- **Development**: See `CLAUDE.md` for development guidelines

---

**Start your private journaling journey today. Your thoughts, your data, your device.**