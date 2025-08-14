# DANA - safe journal space

A privacy-first desktop journaling application with warm, companion-like AI insights. Write, reflect, and discover patterns in your thoughts with Dana's supportive guidance while keeping all data on your device.

![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-macOS%20|%20Windows%20|%20Linux-green.svg)

## 🌟 Features

### Core Functionality (Available Now)
- **Privacy-First Design**: 100% local operation - all your data stays on your device
- **Interactive Calendar**: Visual month navigation with entry indicators and date selection
- **Enhanced Markdown Editor**: Rich text editing with formatting toolbar and auto-save
- **Smart Organization**: Automatic file organization by date (YYYY/MM/DD structure)
- **Dual-Mode Setup**: Create new vaults or load existing journal folders
- **DANA's Companion Interface**: Warm, supportive dark theme optimized for focused writing
- **Collapsible Wisdom Cards**: AI-powered insights with enhanced regeneration UX (infrastructure ready)

### Coming Soon
- **Dana's Wisdom**: AI-powered companion insights with warm, supportive guidance
- **Pattern Recognition**: Discover themes and emotional patterns in your writing
- **Advanced Search**: Full-text search across all entries
- **Growth Tracking**: Personal reflection and emotional pattern analysis

## 🚀 Quick Start

### Installation Options

#### Option 1: Pre-built Packages (Recommended)
Download the latest release for your platform:

- **macOS**: Download `dana-journal.app` and drag to Applications folder
- **Windows**: Download and run `dana-journal.exe` installer  
- **Linux**: Download `dana-journal` executable and make it executable
- **Web**: Access the Progressive Web App at [your-web-url]

#### Option 2: From Source (Development)

##### Prerequisites
- **Python 3.11 or higher**
- **uv package manager** (for dependency management)

##### Build from Source
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

3. **Build the application:**
   ```bash
   # Quick development build for current platform
   ./scripts/build.sh dev
   
   # Or production build
   ./scripts/build.sh macos    # for macOS
   ./scripts/build.sh windows  # for Windows
   ./scripts/build.sh linux    # for Linux
   ```

### Running the Application

#### First Time Setup (with onboarding)
```bash
uv run python -m dana_journal.main
```

This will guide you through the 4-step onboarding process:
1. **Welcome**: Learn about DANA's features and privacy principles
2. **Privacy**: Understand local-only data processing
3. **Storage**: Choose between creating a new vault or loading an existing one
4. **AI Setup**: Optional download of AI model for Dana's Wisdom features

#### Reset Onboarding (for testing)
```bash
# Reset the onboarding state
uv run python tests/reset_onboarding.py

# Then run the app
uv run python -m dana_journal.main
```

#### Skip Onboarding (after first setup)
Once you've completed onboarding, simply run:
```bash
uv run python -m dana_journal.main
```

The app will remember your settings and open directly to the main interface.

## 🏗️ Development

### Project Structure

```
src/dana_journal/
├── main.py              # Main application entry point
├── config/
│   └── app_config.py    # Configuration management
├── ui/
│   ├── theme.py         # Dark theme system with sage accents
│   └── components/      # Reusable UI components
│       ├── onboarding.py    # 4-step setup wizard with AI setup
│       ├── calendar.py      # Interactive calendar
│       ├── text_editor.py   # Enhanced markdown text editor
│       ├── file_explorer.py # File navigation
│       └── ai_reflection.py # Dana's collapsible wisdom component
├── storage/             # File management system
└── ai/                  # AI integration (99% complete)
    ├── download_model.py    # AI model download manager
    └── prompts.py           # Prompt engineering system
```

### Development Commands

```bash
# Install development dependencies
uv sync

# Run the application
uv run python -m dana_journal.main

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code  
uv run ruff check .

# Reset onboarding for testing
uv run python tests/reset_onboarding.py
```

### Packaging and Distribution

#### Build Commands
```bash
# Quick development build for current platform
./scripts/build.sh dev

# Production builds for specific platforms
./scripts/build.sh macos      # macOS .app bundle
./scripts/build.sh windows    # Windows .exe installer
./scripts/build.sh linux      # Linux executable
./scripts/build.sh web        # Progressive Web App

# Build all supported platforms
./scripts/build.sh all

# Clean build artifacts
./scripts/build.sh clean
```

#### Version Management
```bash
# Show current version and next possible versions
python scripts/version.py current

# Bump version (patch/minor/major)
python scripts/version.py bump patch        # 0.1.0 → 0.1.1
python scripts/version.py bump minor        # 0.1.0 → 0.2.0
python scripts/version.py bump major        # 0.1.0 → 1.0.0

# Create release with git tag
python scripts/version.py release minor
```

#### Complete Release Workflow
```bash
# Create patch release with all platforms
./scripts/package.sh release-patch

# Build and package all platforms
./scripts/package.sh build-all

# Validate build environment
./scripts/package.sh check-health

# Generate checksums for distribution
./scripts/package.sh generate-checksums
```

#### Build Requirements

##### For all platforms:
- Python 3.11+, uv, Git

##### For macOS builds:
- Xcode Command Line Tools: `xcode-select --install`
- CocoaPods: `sudo gem install cocoapods`

##### For Windows builds:
- Visual Studio Build Tools with C++ components
- Windows 10 SDK

##### For Linux builds:
- Build essentials: `sudo apt-get install build-essential`
- GTK development: `sudo apt-get install libgtk-3-dev`

### Data Storage Format

Journal entries are stored as markdown files with YAML frontmatter:

```
Your Journal Directory/
├── .dana_journal/
│   ├── config.json          # App settings
│   ├── index.sqlite         # Entry indexing (implemented)
│   ├── models/              # AI model storage
│   └── ai_cache/            # AI reflection cache (ready)
└── entries/
    └── YYYY/MM/
        └── YYYY-MM-DD.md    # Daily journal entries with wisdom data
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

Configuration is automatically managed in `~/.dana_journal/config.json`:

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
- Creates a new folder structure with `.dana_journal/` metadata
- Perfect for starting fresh

#### Load Existing Vault
- Smart detection of existing journal structures
- Supports both confirmed vaults (with `.dana_journal/`) and compatible folders
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

# Remove .dana_journal directory for fresh testing
rm -rf ~/.dana_journal
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

DANA features a warm, companion-like dark theme with:

- **Left Sidebar**: Calendar and file explorer
- **Main Area**: Enhanced markdown text editor with formatting toolbar
- **Dana's Wisdom**: Collapsible wisdom cards with smooth animations
- **Color Scheme**: Deep midnight backgrounds with sage green accents (#81B29A)
- **Typography**: Clean, readable fonts with companion-like language
- **Responsive Layout**: Space-efficient design that adapts to different window sizes

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

**Start your private journaling journey with Dana today. Your thoughts, your data, your device, your companion.**