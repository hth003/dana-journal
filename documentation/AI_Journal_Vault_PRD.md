# AI Journal Vault - Product Requirements Document

## Table of Contents

1. [Product Overview](#product-overview)
2. [Dark Theme System](#dark-theme-system)
3. [Comprehensive Onboarding Flow](#comprehensive-onboarding-flow)
4. [Main Application Layout](#main-application-layout)
5. [Interactive Calendar Component](#interactive-calendar-component)
6. [Enhanced Text Editor](#enhanced-text-editor)
7. [File Explorer Component](#file-explorer-component)
8. [Configuration Management](#configuration-management)
9. [File-Based Storage System](#file-based-storage-system)
10. [Auto-Save System](#auto-save-system)
11. [Application Architecture](#application-architecture)
12. [Development and Testing](#development-and-testing)

---

## Product Overview

AI Journal Vault is a privacy-first desktop journaling application built with Python and Flet. The application provides local AI-powered insights while keeping all user data on their device. It features a dark-mode Obsidian-inspired interface with comprehensive journaling capabilities.

**Core Philosophy**: Complete privacy with local storage, no accounts required, and local AI processing when possible.

**Target Platform**: Cross-platform desktop application (primary focus on macOS with native integration)

**Current Version**: 0.1.0

---

## Dark Theme System

### Overview
A sophisticated dark theme system providing consistent styling and colors for a focused, calming journaling experience.

### Key Features

#### Color Palette
- **Core Colors**: Deep midnight background (#0A0E1A), warm dark slate surfaces (#1A1F2E), violet primary (#8B5CF6)
- **Text Hierarchy**: Pure off-white primary text (#F8FAFC), light gray secondary (#CBD5E1), muted gray (#94A3B8)
- **State Colors**: Success green (#10B981), warning amber (#F59E0B), error red (#EF4444), info blue (#3B82F6)
- **Interactive States**: Subtle hover effects with primary color variations

#### Typography Scale
- **Scale System**: Based on 1.25 (Major Third) ratio for visual harmony
- **Sizes**: Display (48px), H1 (38px), H2 (30px), H3 (24px), H4 (19px), Body XL (16px), Body (14px), Body SM (12px), Caption (10px)
- **Line Heights**: Tight (1.2) for headlines, Normal (1.4) for body text, Relaxed (1.6) for long-form content

#### Component System
- **Themed Containers**: Automatic background color application based on variant (surface, background, surface_variant, primary)
- **Themed Text**: Automatic color application based on variant (primary, secondary, muted, on_primary)
- **Themed Cards**: Consistent elevation and styling with shadow system
- **Themed Buttons**: Multiple variants (primary, secondary, ghost) with consistent sizing

#### Layout System
- **Spacing Scale**: Based on 8px grid system (xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px, 2xl: 40px, 3xl: 48px, 4xl: 64px)
- **Elevation System**: Five levels (none, sm, md, lg, xl) with consistent shadow implementation
- **Border Radius**: Consistent rounded corners (sm: 4px, md: 8px, lg: 12px, xl: 16px, full: 9999px)
- **Component Sizes**: Standardized sizing for buttons, inputs, icons, and layout elements

### Technical Implementation
- Single theme manager class with always-dark mode
- Automatic color application through themed components
- Consistent shadow and elevation system
- Typography scale with proper font weights and line heights

---

## Comprehensive Onboarding Flow

### Overview
A sophisticated 3-step onboarding process that guides new users through app setup with dual-mode vault configuration.

### Step 1: Welcome Screen
- **App Introduction**: Large book icon with "AI Journal Vault" title
- **Feature Highlights**: 
  - Complete Privacy (🔒): All data stays on device
  - AI Insights (🤖): Thoughtful reflections on entries
  - Smart Calendar (📅): Visualize journaling journey
- **Visual Design**: Clean card layout with emoji icons and descriptive text

### Step 2: Privacy Explanation
- **Privacy Emphasis**: Shield icon with "Your Privacy Matters" heading
- **Key Privacy Points**:
  - Local Storage Only (🏠): No external servers
  - No Account Required (🚫): No sign-ups or data collection
  - Local AI Processing (🤖): Keeps thoughts private
- **Trust Building**: Detailed explanations of privacy measures

### Step 3: Dual-Mode Vault Setup
- **Mode Selection**: Radio button choice between "Create New Vault" and "Load Existing Vault"

#### Create New Vault Mode
- **Vault Naming**: Text input with default "My Journal" name
- **Storage Location**: 
  - Browse button for custom directory selection
  - "Use Documents" button for default location
  - Real-time path preview showing final vault location
- **Native Integration**: macOS native folder picker using osascript
- **Path Validation**: Write permission verification and error handling

#### Load Existing Vault Mode
- **Smart Detection**: Recognizes existing vault structures
  - Confirmed vaults (contains .journal_vault directory)
  - Compatible vaults (contains entries folder structure with YYYY/MM/*.md files)
- **Vault Type Indicators**: Visual confirmation of vault type
- **Browse Functionality**: Native folder picker for vault selection
- **Validation**: Comprehensive structure validation with helpful error messages

### Technical Features
- **Progress Indicator**: Visual step progression with connected circles
- **Native macOS Integration**: osascript-based folder selection
- **Error Handling**: Comprehensive error messages and fallback options
- **Alias Path Conversion**: Proper handling of macOS alias paths
- **Real-time Updates**: Live path preview and validation feedback

---

## Main Application Layout

### Overview
Obsidian-inspired three-panel layout optimized for journaling workflow with consistent dark theming.

### Layout Structure

#### Header Section
- **App Title**: "AI Journal Vault" with primary color styling
- **Consistent Spacing**: Professional header with proper typography hierarchy
- **Border Treatment**: Subtle bottom border for visual separation

#### Left Sidebar (280px width)
- **Calendar Section**: Interactive month calendar with entry indicators
- **File Explorer Section**: Hierarchical file browser with search functionality
- **Visual Separation**: Subtle divider between sections
- **Consistent Padding**: Proper spacing throughout sidebar

#### Main Content Area
- **Journal Entry Section**: 
  - Dynamic entry title with date formatting
  - Enhanced text editor with full-screen capability
  - Manual save button with visual feedback
- **AI Reflection Section**: 
  - Placeholder for AI-powered insights
  - Card-based layout with consistent theming
- **Visual Separation**: Horizontal divider between sections

### State Management
- **Window State Persistence**: Saves and restores window size and position
- **Date Selection**: Synchronized across calendar and file explorer
- **Entry Loading**: Automatic content loading when switching dates
- **Auto-save Integration**: Real-time saving with visual indicators

### Technical Implementation
- **Responsive Layout**: Proper container sizing and expansion
- **Component Integration**: Seamless communication between UI components
- **Theme Consistency**: Unified dark theme application across all panels
- **Performance**: Efficient updates and rendering

---

## Interactive Calendar Component

### Overview
A sophisticated calendar component that provides intuitive date navigation, entry visualization, and seamless integration with the journaling system.

### Core Features

#### Monthly Navigation
- **Month Display**: 3-character month abbreviation (e.g., "Aug 2024") for compact display
- **Navigation Controls**: Previous/next month buttons with hover states
- **Today Button**: Quick navigation to current date with primary color styling
- **Responsive Design**: Optimized button sizes and spacing

#### Calendar Grid
- **Weekday Headers**: Abbreviated weekday labels (Mon-Sun) with consistent styling
- **Date Display**: Clickable date cells with multiple visual states
- **Compact Layout**: Optimized spacing (32x28px cells) for sidebar integration
- **Visual Hierarchy**: Clear typography with proper font weights

#### Entry Indicators
- **Entry Dots**: Small amber dots (3px) indicating days with journal entries
- **Today Highlight**: Primary color background for current date
- **Selection State**: Primary color background for selected date
- **Dynamic Updates**: Real-time indicator updates when entries are created/deleted

#### Interactive States
- **Hover Effects**: Smooth hover transitions with themed colors
- **Click Feedback**: Visual feedback on date selection
- **Keyboard Support**: Arrow key navigation (planned enhancement)
- **Animation**: Smooth state transitions (100ms ease-out)

### Visual Design
- **Color System**: Integrated with dark theme palette
- **Legend**: Clear indicators explaining dot meanings
- **Consistent Styling**: Matches overall application design language
- **Accessibility**: High contrast ratios and clear visual feedback

### Technical Implementation
- **Date Management**: Proper datetime handling for date operations
- **State Synchronization**: Automatic updates when entry dates change
- **Performance**: Efficient grid rendering and updates
- **Integration**: Seamless communication with main application

### Mini Calendar Variant
- **Compact Version**: Smaller variant for space-constrained layouts
- **Simplified Interface**: Reduced feature set optimized for smaller spaces
- **Consistent Behavior**: Same core functionality in compact form factor

---

## Enhanced Text Editor

### Overview
A sophisticated markdown-aware text editor with auto-save functionality, writing statistics, and formatting shortcuts designed for an optimal journaling experience.

### Core Features

#### Text Input
- **Rich Text Field**: Multiline text input with markdown support
- **Syntax Highlighting**: (Planned) Markdown syntax highlighting
- **Placeholder Text**: Dynamic placeholder based on selected date
- **Font System**: System font stack for optimal readability
- **Line Height**: 1.7 ratio for improved readability

#### Formatting Toolbar
- **Bold Formatting**: Bold button with Ctrl+B shortcut
- **Italic Formatting**: Italic button with Ctrl+I shortcut
- **Link Creation**: Link button with Ctrl+K shortcut
- **Heading Levels**: H1, H2, H3 buttons with Ctrl+1/2/3 shortcuts
- **Visual Separation**: Dividers between button groups
- **Hover States**: Consistent hover feedback

#### Writing Statistics
- **Word Count**: Real-time word counting with accurate tokenization
- **Character Count**: Both with and without spaces
- **Paragraph Count**: Automatic paragraph detection
- **Reading Time**: Estimated reading time (250 words per minute)
- **Visual Display**: Clean statistics bar with dividers

#### Auto-Save System
- **Debounced Saving**: Prevents excessive file writes
- **Visual Indicators**: Save status with icon and text feedback
- **Blur Trigger**: Saves on focus loss for data safety
- **Manual Save**: Force save button for user control
- **Change Tracking**: Dirty state detection and display

### Advanced Features

#### Markdown Support
- **Formatting Shortcuts**: Quick insertion of markdown syntax
- **Smart Insertion**: Context-aware formatting insertion
- **Selection Handling**: Wraps selected text with formatting
- **Placeholder Text**: Provides examples for markdown elements

#### User Experience
- **Cursor Management**: Proper cursor positioning after formatting
- **Undo/Redo**: (Planned) Full undo/redo stack
- **Find/Replace**: (Planned) Text search and replace functionality
- **Spell Check**: (Planned) Integrated spell checking

### Technical Implementation
- **Component Architecture**: Modular design with separate managers
- **State Management**: Clean separation of content and UI state
- **Performance**: Efficient text processing and UI updates
- **Accessibility**: Keyboard shortcuts and screen reader support

### Statistics Classes
- **WritingStats**: Calculates word, character, and paragraph counts
- **AutoSaveManager**: Handles debounced saving with async support
- **MarkdownHelper**: Provides formatting assistance methods

---

## File Explorer Component

### Overview
A comprehensive file browsing system that organizes journal entries in a hierarchical structure with search functionality and intuitive navigation.

### Core Features

#### Hierarchical File Tree
- **Root Structure**: "Entries" root node containing all journal entries
- **Year Grouping**: Entries organized by year in descending order (newest first)
- **Month Organization**: Months displayed as "MM - Month Name" (e.g., "08 - August")
- **Entry Display**: Individual entries shown as "DD - Weekday" (e.g., "15 - Monday")
- **Expandable Nodes**: Click to expand/collapse year and month folders

#### Visual Design
- **Icons**: Folder icons for directories, document icons for entries
- **Color Coding**: Different colors for expanded/collapsed states
- **Selection States**: Visual feedback for selected entries
- **Depth Indentation**: Clear visual hierarchy with proper indentation
- **Hover Effects**: Interactive feedback on all clickable elements

#### Search Functionality
- **Real-time Search**: Live search as user types (minimum 2 characters)
- **Content Search**: Searches both entry titles and content
- **Result Display**: Clean search results with entry previews
- **Result Navigation**: Click to jump directly to search result
- **Search Clear**: Automatic return to tree view when search is cleared

#### File Operations
- **New Entry**: Create new journal entry for current date
- **Entry Selection**: Click to load entry content
- **Refresh**: Manual refresh to update file tree
- **Date Navigation**: Automatic expansion to show selected date

### Advanced Features

#### Smart Navigation
- **Auto Expansion**: Current month expanded by default
- **Path Expansion**: Automatic expansion to show selected entry
- **Selection Sync**: Synchronized with calendar component selection
- **Recent First**: Entries sorted by date (newest to oldest)

#### Search Results
- **Preview Text**: Shows first 100 characters of entry content
- **Date Context**: Clear date display for each result
- **Hit Highlighting**: (Planned) Highlight search terms in results
- **Result Ranking**: (Planned) Relevance-based result ordering

### Technical Implementation

#### File Tree Structure
- **FileTreeNode Class**: Represents tree structure with parent/child relationships
- **Depth Calculation**: Automatic depth calculation for indentation
- **State Management**: Expansion state tracking for nodes
- **Performance**: Efficient tree building and updates

#### Search Integration
- **Database Integration**: Leverages SQLite index for fast search
- **Content Scanning**: Full-text search capability
- **Result Limiting**: Prevents performance issues with large datasets
- **Error Handling**: Graceful handling of search errors

#### UI Components
- **Dynamic Updates**: Real-time tree updates when entries change
- **Component Lifecycle**: Proper initialization and cleanup
- **Event Handling**: Robust click and interaction handling
- **Accessibility**: Keyboard navigation support (planned)

---

## Configuration Management

### Overview
Persistent application configuration system that maintains user preferences, onboarding status, and application state across sessions.

### Core Features

#### Configuration Storage
- **Location**: `~/.journal_vault/config.json`
- **Format**: JSON-based configuration file
- **Auto-Creation**: Automatic configuration directory creation
- **Error Handling**: Graceful handling of corrupted configuration files

#### Onboarding Management
- **Status Tracking**: Boolean flag for onboarding completion
- **Vault Configuration**: Storage path and vault name persistence
- **First-Run Detection**: Automatic onboarding trigger for new users
- **Setup Validation**: Ensures proper configuration before main app launch

#### Window State Persistence
- **Size Storage**: Window width and height preservation
- **Position Memory**: (Planned) Window position restoration
- **Maximized State**: (Planned) Maximized window state tracking
- **Default Values**: Sensible defaults (1400x900) for new installations

#### User Preferences
- **Generic System**: Key-value storage for user preferences
- **Type Safety**: Proper type handling for different preference types
- **Default Values**: Configurable default values for preferences
- **Extensibility**: Easy addition of new preference categories

### Advanced Features

#### Configuration Backup
- **Export Function**: Export configuration to external file
- **Import Function**: Import configuration from external file
- **Backup Safety**: Configuration validation before import
- **Migration Support**: (Planned) Version migration for configuration updates

#### Validation System
- **Path Validation**: Ensures storage paths are accessible and writable
- **Data Integrity**: Validates configuration structure and values
- **Error Recovery**: Automatic fallback to defaults on corruption
- **User Feedback**: Clear error messages for configuration issues

### Technical Implementation

#### AppConfig Class
- **Singleton Pattern**: Global configuration instance
- **Lazy Loading**: Configuration loaded on first access
- **Auto-Save**: Automatic saving on configuration changes
- **Thread Safety**: Safe concurrent access to configuration

#### File Operations
- **JSON Handling**: Robust JSON serialization and deserialization
- **File Locking**: (Planned) Prevents concurrent modification issues
- **Atomic Updates**: Safe configuration updates
- **Backup Creation**: (Planned) Automatic backup before modifications

#### API Design
- **Simple Interface**: Easy-to-use getter/setter methods
- **Type Safety**: Type hints for better development experience
- **Error Handling**: Comprehensive error handling and reporting
- **Extensibility**: Easy addition of new configuration categories

---

## File-Based Storage System

### Overview
A comprehensive file-based storage system that manages journal entries as markdown files with YAML frontmatter, providing full data control and portability while maintaining performance through SQLite indexing.

### Core Architecture

#### Storage Structure
```
User's Journal Directory/
├── .journal_vault/
│   ├── config.json          # App settings
│   ├── index.sqlite         # Entry indexing database
│   └── ai_cache/            # AI reflection cache (planned)
└── entries/
    └── YYYY/MM/
        └── YYYY-MM-DD.md    # Journal entries with YAML frontmatter
```

#### File Format
- **Markdown Files**: Human-readable .md files with full markdown support
- **YAML Frontmatter**: Structured metadata at file beginning
- **Portable Format**: Standard formats ensure data portability
- **Version Control**: Git-friendly file structure

### Journal Entry Data Model

#### Core Entry Properties
- **Title**: Entry title with automatic date-based defaults
- **Content**: Full markdown content of the journal entry
- **Date**: Journal date (separate from creation/modification dates)
- **Created At**: Timestamp of entry creation
- **Modified At**: Timestamp of last modification

#### Optional Metadata
- **Tags**: List of tags for categorization and filtering
- **Word Count**: Automatic word count calculation and storage
- **Mood Rating**: Optional integer mood rating (1-10 scale)
- **AI Reflection**: Dictionary containing AI-generated insights
- **Version**: Entry format version for future migrations

#### System Metadata
- **File Path**: Automatic file path management
- **Content Hash**: Hash for change detection
- **Database Sync**: Bidirectional sync between files and database

### Database Indexing

#### SQLite Integration
- **Index Database**: Fast search and filtering capabilities
- **Metadata Storage**: Efficient metadata querying
- **Relationship Tracking**: Entry relationships and dependencies
- **Performance Optimization**: Indexed searches and queries

#### Database Schema
- **Entries Table**: Core entry metadata with optimized indexes
- **Date Indexing**: Fast date-range queries
- **Modification Tracking**: Efficient change detection
- **Full-Text Search**: (Planned) Advanced search capabilities

### File Operations

#### CRUD Operations
- **Create Entry**: New journal entry creation with automatic file structure
- **Load Entry**: Efficient entry loading with frontmatter parsing
- **Save Entry**: Atomic saves with metadata updates
- **Delete Entry**: Safe deletion with database cleanup
- **Rename Entry**: Date changes with file system updates

#### Advanced Operations
- **Bulk Operations**: Efficient handling of multiple entries
- **Search Functionality**: Title and content search with relevance ranking
- **Date Range Queries**: Efficient retrieval of entries within date ranges
- **Statistics Generation**: Comprehensive journaling statistics

### Data Integrity

#### Validation System
- **Vault Structure**: Validates required directories and files
- **Database Integrity**: SQLite integrity checks and repair
- **File Consistency**: Ensures files match database entries
- **Orphan Detection**: Identifies and resolves orphaned files

#### Backup and Recovery
- **Database Backup**: SQLite backup functionality
- **File Scanning**: Rebuilds index from existing files
- **Data Recovery**: Recovers from various corruption scenarios
- **Migration Support**: (Planned) Seamless data format migrations

### Performance Features

#### Optimization Strategies
- **Lazy Loading**: Entries loaded on demand
- **Efficient Indexing**: Fast searches without file system scanning
- **Caching**: (Planned) Intelligent content caching
- **Batch Operations**: Efficient bulk operations

#### Scalability
- **Large Datasets**: Designed to handle thousands of entries
- **Memory Efficiency**: Minimal memory footprint
- **Search Performance**: Sub-second search across large journals
- **File System Efficiency**: Optimal directory structure for file systems

### Technical Implementation

#### FileManager Class
- **Centralized Management**: Single point of control for all file operations
- **Error Handling**: Comprehensive error handling and recovery
- **Type Safety**: Full type hints and data validation
- **Extensibility**: Plugin-ready architecture for future enhancements

#### Data Serialization
- **YAML Processing**: Robust YAML frontmatter handling
- **Encoding Safety**: UTF-8 encoding with proper error handling
- **Format Validation**: Ensures data integrity during serialization
- **Version Compatibility**: Forward and backward compatibility support

---

## Auto-Save System

### Overview
An intelligent auto-save system that provides seamless data persistence while preventing excessive file writes through sophisticated debouncing and change detection mechanisms.

### Core Features

#### Debounced Saving
- **Save Intervals**: Configurable save intervals (default: 30 seconds)
- **Maximum Delay**: Force save after maximum time (default: 5 minutes)
- **Change Detection**: Only saves when meaningful changes are detected
- **Thread Safety**: Safe concurrent access with proper locking

#### Smart Change Detection
- **Content Hashing**: Efficient change detection using content hashes
- **Minimum Changes**: Configurable minimum change threshold (default: 10 characters)
- **Meaningful Content**: Filters out trivial changes (whitespace, empty content)
- **Diff Analysis**: (Planned) Detailed change analysis for optimization

#### Configuration System
- **AutoSaveConfig Class**: Comprehensive configuration management
- **Runtime Changes**: Dynamic configuration updates without restart
- **Per-Entry Settings**: (Planned) Entry-specific auto-save behavior
- **User Preferences**: Integrated with application configuration system

### Advanced Features

#### Queue Management
- **Pending Saves**: Maintains queue of entries awaiting save
- **Priority System**: (Planned) Priority-based save ordering
- **Batch Processing**: (Planned) Efficient batch save operations
- **Resource Management**: Prevents system resource exhaustion

#### Callback System
- **Success Callbacks**: Notifications on successful saves
- **Error Callbacks**: Error handling and notification system
- **Progress Tracking**: Real-time save progress information
- **Event Integration**: Seamless integration with UI components

#### Force Save Capabilities
- **Immediate Save**: Manual force save for single entries
- **Batch Force Save**: Force save all pending entries
- **Application Exit**: Automatic save on application shutdown
- **User Trigger**: Manual save button integration

### Status Monitoring

#### AutoSaveStatus Class
- **Comprehensive Status**: Complete auto-save system status
- **Per-Entry Status**: Individual entry save status tracking
- **Performance Metrics**: Save timing and performance data
- **Health Monitoring**: System health and error tracking

#### Status Information
- **Pending Saves Count**: Number of entries awaiting save
- **Last Save Times**: Timestamp tracking for all entries
- **Save History**: (Planned) Historical save operation data
- **Error Reporting**: Detailed error information and recovery suggestions

### Technical Implementation

#### Threading Architecture
- **Background Processing**: Non-blocking save operations
- **Timer Management**: Efficient timer scheduling and cancellation
- **Lock Coordination**: Proper synchronization for thread safety
- **Resource Cleanup**: Automatic cleanup of completed operations

#### Integration Points
- **Text Editor**: Seamless integration with text editing components
- **File Manager**: Direct integration with file storage system
- **Configuration**: Uses application configuration system
- **UI Feedback**: Real-time status updates in user interface

#### Error Handling
- **Exception Management**: Comprehensive exception handling
- **Recovery Procedures**: Automatic error recovery mechanisms
- **User Notification**: Clear error communication to users
- **Fallback Strategies**: Multiple fallback approaches for save failures

### Performance Characteristics

#### Efficiency Measures
- **Minimal File I/O**: Reduces unnecessary file system operations
- **Memory Efficiency**: Low memory footprint for save operations
- **CPU Optimization**: Efficient change detection algorithms
- **Scalability**: Handles large numbers of concurrent entries

#### Resource Management
- **Timer Optimization**: Efficient timer creation and management
- **Memory Cleanup**: Automatic cleanup of completed save operations
- **System Integration**: Respects system resource limits
- **Battery Efficiency**: (Planned) Power-aware save scheduling for laptops

---

## Application Architecture

### Overview
A well-structured Python application built with Flet framework, featuring modular design, clean separation of concerns, and comprehensive error handling.

### Project Structure

#### Core Application (`main.py`)
- **JournalVaultApp Class**: Main application controller managing UI state and component integration
- **Page Management**: Flet page configuration and window state management
- **Component Orchestration**: Coordinates calendar, editor, and file explorer interactions
- **State Synchronization**: Maintains consistency across all UI components

#### UI System (`ui/`)
- **Theme System** (`theme.py`): Comprehensive dark theme with consistent colors and typography
- **Components** (`components/`): Modular UI components with clear responsibilities
  - **Onboarding** (`onboarding.py`): Multi-step setup process with native integrations
  - **Calendar** (`calendar.py`): Interactive calendar with entry indicators
  - **Text Editor** (`text_editor.py`): Enhanced markdown editor with auto-save
  - **File Explorer** (`file_explorer.py`): Hierarchical file browser with search

#### Storage System (`storage/`)
- **File Manager** (`file_manager.py`): Core file operations with SQLite indexing
- **Auto-Save** (`auto_save.py`): Intelligent auto-save with debouncing
- **Integration** (`integration.py`): Storage system integration layer

#### Configuration (`config/`)
- **App Config** (`app_config.py`): Persistent configuration management
- **Settings Storage**: JSON-based configuration with automatic backup
- **User Preferences**: Extensible preference system

#### AI Integration (`ai/`)
- **Placeholder Structure**: Ready for AI integration with local processing
- **Reflection Engine**: (Planned) Local AI-powered journal insights
- **Privacy-First Design**: All AI processing designed for local execution

### Design Patterns

#### Component Architecture
- **Themed Components**: All UI components inherit from themed base classes
- **Event-Driven Design**: Components communicate through well-defined callbacks
- **State Management**: Clear separation of UI state and application data
- **Dependency Injection**: Components receive dependencies through constructor

#### Error Handling
- **Graceful Degradation**: Application continues functioning despite individual component failures
- **User-Friendly Messages**: Clear error messages with actionable guidance
- **Recovery Mechanisms**: Automatic recovery from common failure scenarios
- **Logging Strategy**: (Planned) Comprehensive logging for debugging

### Integration Features

#### Native Platform Integration
- **macOS Support**: Native folder selection using osascript
- **Window Management**: Proper window state persistence
- **File System**: Optimized file operations for each platform
- **Cross-Platform Design**: Architecture supports multiple desktop platforms

#### Component Communication
- **Callback System**: Type-safe callback interfaces between components
- **Event Propagation**: Proper event handling throughout the component tree
- **State Synchronization**: Automatic state updates across related components
- **Performance Optimization**: Efficient update mechanisms to prevent unnecessary refreshes

### Technical Specifications

#### Dependencies
- **Flet Framework**: Cross-platform UI framework (v0.28.3)
- **Pydantic**: Data validation and settings management (v2.8.0+)
- **Python-Dateutil**: Advanced date handling (v2.9.0+)
- **PyYAML**: YAML frontmatter processing (v6.0.2+)
- **SQLite**: Built-in database for indexing (Python standard library)

#### Development Tools
- **Black**: Code formatting with 88-character line length
- **Ruff**: Fast Python linting and code analysis
- **Pytest**: Comprehensive testing framework with async support
- **Type Hints**: Full type annotation coverage for better development experience

#### Performance Characteristics
- **Startup Time**: Fast application startup with lazy loading
- **Memory Usage**: Efficient memory management with proper cleanup
- **File I/O**: Optimized file operations with batch processing
- **UI Responsiveness**: Non-blocking operations with proper async handling

---

## Development and Testing

### Overview
Comprehensive development environment with modern Python tooling, automated testing, and quality assurance measures.

### Development Environment

#### Package Management
- **UV Tool**: Modern Python package manager for dependency management
- **Project Configuration**: pyproject.toml-based configuration
- **Virtual Environment**: Isolated development environment
- **Dependency Groups**: Separate development and production dependencies

#### Code Quality Tools
- **Black Formatter**: Automatic code formatting with 88-character line length
- **Ruff Linter**: Fast Python linting with comprehensive rule set
- **Type Checking**: Full type hint coverage for better development experience
- **Pre-commit Hooks**: (Planned) Automated quality checks on commit

### Testing Framework

#### Test Structure
- **Pytest Framework**: Modern testing framework with fixture support
- **Async Testing**: pytest-asyncio for testing async functionality
- **Test Discovery**: Automatic test discovery with standard naming conventions
- **Test Organization**: Tests organized in `/tests` directory with clear naming

#### Test Categories
- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: Component interaction testing
- **UI Testing**: (Planned) Automated UI testing with Flet test utilities
- **End-to-End Tests**: (Planned) Complete workflow testing

#### Utility Scripts
- **Onboarding Reset** (`tests/reset_onboarding.py`): Development utility for testing onboarding flow
- **Test Runners**: Individual test execution for specific components
- **Development Helpers**: Scripts for common development tasks

### Build and Deployment

#### Build Configuration
- **Hatchling Backend**: Modern Python package building
- **Cross-Platform Support**: Build configuration for multiple platforms
- **Asset Management**: (Planned) Static asset bundling and optimization
- **Distribution**: (Planned) Application packaging for various platforms

#### Development Commands
```bash
# Start application
uv run python -m journal_vault.main

# Install dependencies
uv sync

# Run tests
uv run pytest

# Code formatting
uv run black .

# Linting
uv run ruff check .

# Reset onboarding for testing
uv run python tests/reset_onboarding.py
```

### Quality Assurance

#### Code Standards
- **Consistent Formatting**: Black formatter ensures consistent code style
- **Linting Rules**: Ruff provides comprehensive code quality checks
- **Type Safety**: Full type hint coverage for better maintainability
- **Documentation**: Comprehensive docstrings and code comments

#### Testing Standards
- **Test Coverage**: (Planned) Comprehensive test coverage reporting
- **Continuous Integration**: (Planned) Automated testing on code changes
- **Performance Testing**: (Planned) Performance benchmarks and regression testing
- **Compatibility Testing**: (Planned) Multi-platform compatibility verification

#### Documentation Standards
- **Code Documentation**: Comprehensive docstrings for all public interfaces
- **Architecture Documentation**: High-level architecture and design decisions
- **User Documentation**: (Planned) User guides and help documentation
- **API Documentation**: (Planned) Generated API documentation

### Development Workflow

#### Feature Development
1. **Local Development**: Feature development in isolated environment
2. **Testing**: Comprehensive testing before integration
3. **Code Review**: (Planned) Peer review process for code changes
4. **Integration**: Safe integration with comprehensive testing

#### Release Process
1. **Version Management**: Semantic versioning for releases
2. **Change Documentation**: Detailed changelog for each release
3. **Testing**: Comprehensive testing before release
4. **Distribution**: (Planned) Automated release distribution

---

This Product Requirements Document comprehensively covers all implemented functionality in the AI Journal Vault codebase, providing detailed specifications for each component and system. The application represents a sophisticated journaling solution with privacy-first design, modern UI architecture, and comprehensive storage management capabilities.