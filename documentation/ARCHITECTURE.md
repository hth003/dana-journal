# AI Journal Vault - Technical Architecture Documentation

This document provides a comprehensive technical overview of the AI Journal Vault architecture, including system design, component interactions, data flows, and architectural decisions.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [System Architecture](#system-architecture)
- [Component Architecture](#component-architecture)
- [Data Flow Diagrams](#data-flow-diagrams)
- [Storage Architecture](#storage-architecture)
- [UI Architecture](#ui-architecture)
- [Configuration Management](#configuration-management)
- [Architecture Decisions](#architecture-decisions)

---

## Architecture Overview

AI Journal Vault is a privacy-first desktop journaling application built with Python and Flet. The architecture follows a modular, layered design with clear separation of concerns between UI, business logic, and data persistence.

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Journal Vault                         │
├─────────────────────────────────────────────────────────────┤
│  Frontend Layer (Flet-based GUI)                           │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │ Onboarding  │   Calendar  │ Text Editor │File Explorer│ │
│  │ Component   │  Component  │  Component  │ Component   │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Application Layer                                          │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │    Theme    │    Main     │   Config    │ Integration │ │
│  │   Manager   │    App      │   Manager   │   Service   │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Storage Layer                                              │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│  │    File     │  Auto-Save  │   Journal   │   SQLite    │ │
│  │   Manager   │   Manager   │   Entries   │   Index     │ │
│  └─────────────┴─────────────┴─────────────┴─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  File System (Local Storage)                               │
│  ~/Documents/Journal Vault/ or User-Selected Path          │
└─────────────────────────────────────────────────────────────┘
```

---

## System Architecture

### Architectural Principles

1. **Privacy First**: All data remains local on the user's device
2. **Modular Design**: Clear separation between UI, business logic, and storage
3. **Event-Driven**: Component communication through callbacks and events
4. **Consistent Theming**: Dark-mode only UI with Obsidian-inspired design
5. **Auto-Save**: Intelligent debounced saving to prevent data loss
6. **File-Based Storage**: Human-readable markdown files with YAML frontmatter

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                 JournalVaultApp (main.py)                  │
│                   Central Coordinator                       │
├─────────────────────────────────────────────────────────────┤
│  • Page state management                                    │
│  • UI component orchestration                               │
│  • Event handling and routing                               │
│  • Window state persistence                                 │
│  • Entry loading/saving coordination                        │
└─────────────────────────────────────────────────────────────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ UI Layer    │       │Storage Layer│       │Config Layer │
│             │       │             │       │             │
│ • Theme Mgmt│       │ • File Mgmt │       │ • App Config│
│ • Components│◄──────┤ • Auto-Save │       │ • User Prefs│
│ • Layout    │       │ • Integration│       │ • Window St │
└─────────────┘       └─────────────┘       └─────────────┘
```

---

## Component Architecture

### UI Components Hierarchy

```
JournalVaultApp
├── OnboardingFlow (conditional)
│   ├── WelcomeStep
│   ├── PrivacyStep
│   └── StorageStep
│
└── MainLayout (post-onboarding)
    ├── Header
    │   └── AppTitle
    ├── LeftSidebar
    │   ├── CalendarComponent
    │   │   ├── MonthNavigation
    │   │   ├── CalendarGrid
    │   │   └── Legend
    │   └── FileExplorer
    │       ├── SearchField
    │       ├── FileTree
    │       └── SearchResults
    ├── MainContent
    │   ├── TextEditor
    │   │   ├── Toolbar
    │   │   ├── TextField
    │   │   └── StatsDisplay
    │   └── AIReflection (planned)
    └── StatusBar (implicit)
```

### Component Details

#### CalendarComponent
- **Purpose**: Interactive month-view calendar with entry indicators
- **Features**: Date selection, month navigation, "Today" button, entry indicators
- **State**: Current month, selected date, entry dates set
- **Events**: Date selection notifications

#### EnhancedTextEditor
- **Purpose**: Markdown-aware text editor with formatting tools
- **Features**: Auto-save, word count, formatting toolbar, writing statistics
- **State**: Content, dirty state, auto-save status
- **Events**: Content changes, save operations

#### FileExplorer
- **Purpose**: Hierarchical file browser for journal entries
- **Features**: Tree view, search, date-based organization, entry creation
- **State**: File tree, search results, selected entry
- **Events**: File selection, entry creation requests

#### OnboardingFlow
- **Purpose**: Multi-step setup wizard for new users
- **Features**: Feature overview, privacy explanation, storage selection
- **State**: Current step, onboarding data
- **Events**: Completion callback with configuration data

### Storage Components

```
StorageIntegrationService
├── FileManager
│   ├── Entry CRUD operations
│   ├── File system organization
│   ├── SQLite indexing
│   └── Search functionality
├── AutoSaveManager
│   ├── Debounced saving
│   ├── Queue management
│   └── Status tracking
└── JournalEntry (Data Model)
    ├── Core content (title, body)
    ├── Metadata (dates, tags)
    └── AI reflection data
```

---

## Data Flow Diagrams

### Entry Creation Flow

```
User Action          UI Component           Storage Layer           File System
     │                    │                     │                      │
     ├─ Date Selected ────┤                     │                      │
     │                    ├─ Load Entry ───────┤                      │
     │                    │                     ├─ Check File ────────┤
     │                    │                     │◄─ File Exists? ─────┤
     │                    │◄─ Entry Found ─────┤                      │
     │                    │   (or null)        │                      │
     ├─ Start Typing ─────┤                     │                      │
     │                    ├─ Content Change ───┤                      │
     │                    │                     ├─ Queue Auto-save ───┤
     │                    │                     │                      │
     │                    │                     ├─ Debounced Save ────┤
     │                    │                     │                      ├─ Write MD File
     │                    │                     │                      ├─ Update SQLite
     │                    │◄─ Save Success ────┤                      │
```

### Application Startup Flow

```
main.py
  │
  ├─ Initialize JournalVaultApp
  │    ├─ Load app_config
  │    ├─ Check onboarding status
  │    │
  │    ├─ IF not onboarded:
  │    │    └─ Show OnboardingFlow
  │    │         ├─ Welcome screen
  │    │         ├─ Privacy explanation  
  │    │         ├─ Storage selection
  │    │         └─ Save config & continue
  │    │
  │    └─ IF onboarded:
  │         ├─ Initialize FileManager
  │         ├─ Create UI components
  │         │    ├─ CalendarComponent
  │         │    ├─ TextEditor
  │         │    └─ FileExplorer
  │         ├─ Set up event handlers
  │         └─ Load initial entry
```

### Auto-Save Flow

```
Text Editor          Auto-Save Manager       File Manager         File System
     │                       │                     │                   │
     ├─ Content Changed ─────┤                     │                   │
     │                       ├─ Queue Save        │                   │
     │                       │   (debounced)      │                   │
     │                       │                    │                   │
     │   After delay...      │                    │                   │
     │                       ├─ Execute Save ─────┤                   │
     │                       │                     ├─ Load/Create ────┤
     │                       │                     ├─ Update Entry ───┤
     │                       │                     ├─ Write File ─────┤
     │                       │                     │                   ├─ .md file
     │                       │                     ├─ Update Index ───┤
     │                       │                     │                   ├─ SQLite
     │                       │◄─ Save Complete ───┤                   │
     │◄─ Update UI Status ───┤                     │                   │
```

---

## Storage Architecture

### File System Organization

```
Journal Vault Directory/
├── .journal_vault/                 # Hidden metadata directory
│   ├── config.json                # App settings and preferences  
│   ├── index.sqlite               # Entry indexing and metadata
│   └── ai_cache/                  # AI reflection cache (planned)
│       └── {date-hash}.json
└── entries/                       # User-visible journal entries
    └── YYYY/                      # Year directories
        └── MM/                    # Month directories
            └── YYYY-MM-DD.md      # Daily journal entries
```

### Entry File Format

Each journal entry is stored as a Markdown file with YAML frontmatter:

```yaml
---
title: "Journal Entry - August 07, 2025"
created_at: "2025-08-07T10:30:00"
modified_at: "2025-08-07T14:45:00"
tags: ["reflection", "work", "goals"]
word_count: 256
mood_rating: 7
version: 1
ai_reflection:
  generated_at: "2025-08-07T15:00:00"
  themes: ["productivity", "learning"]
  insights: "User showed growth mindset..."
---

# Today's Reflections

This is the actual journal content written by the user.
It supports **markdown formatting** and can be as long as needed.

## Key Moments
- Morning meditation session
- Important meeting with team
- Evening reading time
```

### Database Schema

SQLite index for fast querying and metadata storage:

```sql
CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,           -- ISO date string
    file_path TEXT NOT NULL,             -- Full file path
    title TEXT,                          -- Entry title
    word_count INTEGER DEFAULT 0,        -- Word count
    created_at TEXT NOT NULL,            -- ISO datetime
    modified_at TEXT NOT NULL,           -- ISO datetime
    tags TEXT,                           -- JSON array of tags
    mood_rating INTEGER,                 -- 1-10 mood scale
    has_ai_reflection BOOLEAN DEFAULT FALSE,
    content_hash TEXT,                   -- MD5 hash for change detection
    version INTEGER DEFAULT 1           -- Schema version
);

CREATE INDEX idx_date ON entries(date);
CREATE INDEX idx_modified ON entries(modified_at);
```

### Data Models

#### JournalEntry Class
```python
@dataclass
class JournalEntry:
    # Core content
    title: str
    content: str
    
    # Metadata
    created_at: datetime
    modified_at: datetime
    date: date
    
    # Optional metadata
    tags: List[str] = None
    word_count: int = 0
    mood_rating: Optional[int] = None
    ai_reflection: Optional[Dict[str, Any]] = None
    
    # System metadata
    version: int = 1
    file_path: Optional[Path] = None
```

---

## UI Architecture

### Theme System

The application uses a comprehensive dark theme system with consistent design tokens:

```python
@dataclass
class DarkTheme:
    # Core colors
    background: str = "#0A0E1A"          # Deep midnight
    surface: str = "#1A1F2E"            # Dark slate
    surface_variant: str = "#2A3441"    # Elevated surface
    primary: str = "#8B5CF6"            # Violet accent
    
    # Text hierarchy
    text_primary: str = "#F8FAFC"       # High contrast
    text_secondary: str = "#CBD5E1"     # Medium contrast
    text_muted: str = "#94A3B8"         # Low contrast
    
    # Interactive states
    hover: str = "#8B5CF610"            # Subtle hover
    selected: str = "#8B5CF620"         # Selection state
    focus: str = "#8B5CF640"            # Focus indicator
```

### Design Token System

```python
# Typography Scale (Major Third - 1.25 ratio)
TYPO_SCALE = {
    "display": 48,    "h1": 38,     "h2": 30,     "h3": 24,
    "h4": 19,         "body_xl": 16, "body": 14,   "body_sm": 12,
    "caption": 10,
}

# Spacing Scale (8px grid system)
SPACING = {
    "xs": 4,    "sm": 8,    "md": 16,   "lg": 24,
    "xl": 32,   "2xl": 40,  "3xl": 48,  "4xl": 64,
}

# Component Dimensions
COMPONENT_SIZES = {
    "sidebar_width": 280,
    "calendar_day_size": 32,
    "button_height": 36,
    "input_height": 40,
}
```

### Themed Components

All UI components inherit from themed base classes:

- **ThemedContainer**: Applies background colors, elevation, spacing
- **ThemedText**: Handles typography, color variants
- **ThemedCard**: Provides consistent elevation and borders
- **ThemedButton**: Standardized interactive elements

### Layout Structure

The main interface follows an Obsidian-inspired three-panel layout:

```
┌─────────────────────────────────────────────────────────────┐
│                        Header Bar                           │
├─────────────┬─────────────────────────────┬─────────────────┤
│             │                             │                 │
│ Left Panel  │      Main Content Area      │  (Future: AI)   │
│             │                             │                 │
│ ┌─────────┐ │ ┌─────────────────────────┐ │                 │
│ │Calendar │ │ │                         │ │                 │
│ │Component│ │ │     Text Editor         │ │                 │
│ └─────────┘ │ │                         │ │                 │
│             │ └─────────────────────────┘ │                 │
│ ┌─────────┐ │                             │                 │
│ │  File   │ │ ┌─────────────────────────┐ │                 │
│ │Explorer │ │ │   AI Reflection Area    │ │                 │
│ └─────────┘ │ │      (Planned)          │ │                 │
│             │ └─────────────────────────┘ │                 │
└─────────────┴─────────────────────────────┴─────────────────┘
```

---

## Configuration Management

### Configuration Architecture

```python
class AppConfig:
    """Persistent application configuration"""
    
    # Storage locations
    config_dir: Path = Path.home() / ".journal_vault"
    config_file: Path = config_dir / "config.json"
    
    # Configuration categories
    def is_onboarded(self) -> bool          # Setup status
    def get_storage_path(self) -> str       # Journal location
    def get_window_state(self) -> dict      # Window geometry
    def get_preference(self, key) -> Any    # User preferences
```

### Configuration File Structure

```json
{
  "onboarded": true,
  "storage_path": "/Users/username/Documents/Journal Vault",
  "window_state": {
    "width": 1400,
    "height": 900,
    "maximized": false
  },
  "preferences": {
    "auto_save_interval": 30,
    "show_word_count": true,
    "default_entry_title_format": "Journal Entry - {date}"
  }
}
```

### Configuration Persistence

- **Automatic Saving**: Configuration changes are immediately persisted
- **Error Handling**: Graceful fallbacks for corrupted configuration files
- **Migration Support**: Version-aware configuration loading
- **Export/Import**: User can backup and restore settings

---

## Architecture Decisions

### 1. Framework Selection: Flet

**Decision**: Use Flet for cross-platform desktop GUI

**Rationale**:
- Python-native development (no context switching)
- Cross-platform support (macOS, Windows, Linux)
- Modern, responsive UI capabilities
- Active development and Flutter backing
- Suitable for privacy-focused local applications

**Trade-offs**:
- ✅ Rapid development in pure Python
- ✅ Consistent UI across platforms  
- ✅ Good performance for document editing
- ❌ Less ecosystem maturity than Electron
- ❌ Limited native platform integration

### 2. Storage Strategy: File-Based with SQLite Index

**Decision**: Store entries as markdown files with SQLite indexing

**Rationale**:
- **User Ownership**: Files remain readable without the application
- **Version Control**: Users can track changes with git
- **Backup Friendly**: Standard file system backup tools work
- **Fast Queries**: SQLite index enables quick searching
- **Human Readable**: Markdown format is universally supported

**Alternative Considered**: Pure database storage
- ❌ Would lock users into proprietary format
- ❌ Harder to backup and migrate
- ❌ Less transparent data ownership

### 3. Auto-Save Architecture: Debounced Background Saving

**Decision**: Implement intelligent auto-save with debouncing

**Rationale**:
- **Data Safety**: Prevents loss during crashes or unexpected exits
- **Performance**: Debouncing prevents excessive file I/O
- **User Experience**: No interruptions to writing flow
- **Configurable**: Users can adjust save intervals

**Implementation Details**:
- 30-second default debounce delay
- Maximum 5-minute forced save interval
- Thread-safe queue management
- Graceful error handling and retry logic

### 4. UI Architecture: Component-Based with Event System

**Decision**: Modular component architecture with callback-based communication

**Rationale**:
- **Maintainability**: Clear separation of concerns
- **Testability**: Components can be tested in isolation
- **Reusability**: UI components can be reused across contexts
- **Event-Driven**: Loose coupling between components

**Communication Pattern**:
```python
# Parent coordinates child components via callbacks
calendar_component = CalendarComponent(
    theme_manager=theme,
    on_date_selected=self._on_date_selected
)

def _on_date_selected(self, date: datetime) -> None:
    """Coordinate response to date selection"""
    self._load_entry_for_date(date)
    self._update_text_editor(date)
    self.file_explorer.select_date(date)
```

### 5. Theme System: Dark Mode Only

**Decision**: Implement single dark theme instead of light/dark toggle

**Rationale**:
- **Focus**: Reduces complexity and decision fatigue
- **Consistency**: Ensures all components work well together
- **User Experience**: Dark themes are preferred for writing applications
- **Development Speed**: Single theme allows faster iteration

**Design Philosophy**:
- Obsidian-inspired color palette
- High contrast for accessibility
- Subtle gradations for visual hierarchy
- Consistent interaction states

### 6. Entry Organization: Date-Based Hierarchy

**Decision**: Organize entries by Year/Month/Day folder structure

**Rationale**:
- **Intuitive Navigation**: Users naturally think chronologically
- **File System Friendly**: Folder structure works with OS tools
- **Scalable**: Performance remains good with thousands of entries
- **Backup Efficient**: Incremental backups work naturally

**Directory Structure**:
```
entries/
├── 2024/
│   ├── 01/  # January
│   │   ├── 2024-01-01.md
│   │   └── 2024-01-15.md
│   └── 02/  # February
│       └── 2024-02-28.md
└── 2025/
    └── 08/
        └── 2025-08-07.md
```

### 7. Configuration Management: JSON with Automatic Migration

**Decision**: Use JSON configuration files with version-aware loading

**Rationale**:
- **Human Readable**: Users can understand and manually edit if needed
- **Standard Format**: Well-supported across platforms
- **Validation**: Easy to validate structure and migrate versions
- **Performance**: Fast loading and saving

**Migration Strategy**:
- Semantic versioning for configuration schema
- Automatic migration on application startup
- Graceful fallbacks for invalid configurations
- Export/import functionality for user control

---

This architecture documentation provides a comprehensive technical overview of the AI Journal Vault system. The modular design, privacy-focused approach, and thoughtful architectural decisions create a solid foundation for a user-friendly, maintainable journaling application.

For implementation details of specific components, refer to the source code in the `src/journal_vault/` directory.