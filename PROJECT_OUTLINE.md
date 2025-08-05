# AI Journal Vault - Project Outline

## Project Overview

**App Name:** AI Journal Vault

**Vision:** A privacy-first desktop journaling application that combines traditional diary writing with local AI-powered insights, ensuring all personal data remains on the user's device while providing meaningful reflection and pattern recognition.

## Core Principles

### Privacy-First Design
- 100% local operation (no internet requirement after initial setup)
- All personal data remains on user's device
- No cloud storage or external data transmission
- User chooses local storage location during onboarding

### Technology Stack
- **Framework:** Python + Flet (cross-platform desktop app)
- **Package Manager:** uv (fast dependency management)
- **AI Model:** Qwen2.5-3B-Instruct (Q4_K_M quantized, bundled)
- **Storage:** Local file system (markdown with YAML frontmatter + SQLite index)
- **Platforms:** Windows, macOS, Linux

## MVP Feature Set

### Core Features (MVP Scope)
✅ **Journal Entry Management**
- Create, edit, delete journal entries
- Markdown editor with live preview
- Auto-save functionality (30-second intervals)

✅ **Calendar Navigation**
- Month view with entry indicators
- Date selection for viewing/creating entries
- Visual dots for dates with existing entries
- Navigation between months

✅ **AI Reflection Engine**
- Generate insights from journal entries
- Provide 3 thoughtful reflection questions per entry
- Local AI processing using bundled Qwen2.5-3B-Instruct

✅ **Local Storage**
- User selects storage location during onboarding
- Markdown files with metadata
- Organized directory structure by year/month

✅ **User Interface**
- Left panel: Calendar view
- Right panel: Journal editor
- Bottom panel: AI reflection
- Dark/light mode themes
- Violet/indigo color scheme

### Features Excluded from MVP
❌ Search functionality (planned for future)
❌ Export features (entries already in portable format)
❌ Cloud sync or backup
❌ Multi-user support
❌ Plugin system

## Technical Architecture

### Project Structure
```
ai-journal-vault/
├── pyproject.toml              # uv configuration
├── src/journal_vault/
│   ├── __init__.py
│   ├── main.py                 # Application entry point + main app class
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── theme.py            # Theme system and styling
│   │   └── components/         # UI components (calendar, editor, etc.)
│   ├── storage/
│   │   └── __init__.py         # File management
│   ├── ai/
│   │   └── __init__.py         # Qwen2.5-3B integration
│   └── config/
│       └── __init__.py         # App settings
├── models/qwen2.5-3b-q4/       # Bundled AI model (quantized)
└── tests/                      # Test suite
```

### AI Integration Strategy
- **Model:** Qwen2.5-3B-Instruct (Q4_K_M quantized)
- **Rationale:** Superior emotional intelligence (4.6/5) and psychological insights
- **Size:** ~1.9GB after quantization (60% size reduction)
- **Performance:** ~9.5 seconds generation time, 2.1GB RAM usage
- **Integration:** Bundled quantized model with llama.cpp
- **Loading:** Lazy loading with progress indicators to prevent UI blocking
- **Processing:** Local inference only, no internet required
- **Caching:** Store reflections with content hashing to avoid regeneration
- **License:** Apache 2.0 (commercial-friendly)

### Data Storage Format
```
User's Journal Directory/
├── .journal_vault/
│   ├── config.json             # App settings
│   ├── index.sqlite            # SQLite index for fast lookups
│   └── ai_cache/               # Cached AI reflections
└── entries/
    └── YYYY/MM/
        └── YYYY-MM-DD.md       # Journal entry with YAML frontmatter
```

#### **YAML Frontmatter Schema**
```yaml
---
title: "My Journal Entry"
created_at: "2024-08-04T10:30:00Z"
modified_at: "2024-08-04T10:45:00Z"
tags: ["reflection", "work", "mood:positive"]
word_count: 1247
ai_reflection:
  model_used: "qwen2.5-3b"
  generated_at: "2024-08-04T10:46:00Z"
  cached: true
mood_rating: 7
version: 1
---
```

## User Experience Design

### UI Layout
```
┌─────────────────────────────────────┐
│  AI Journal Vault      [⚙️] [❓] [🌙] │
├─────────┬───────────────────────────┤
│         │                           │
│ Calendar│      Journal Entry        │
│  View   │        Editor             │
│         │    (Markdown + Preview)   │
│         ├───────────────────────────┤
│         │    AI Reflection Panel    │
│         │   • Insights              │
│         │   • Questions             │
└─────────┴───────────────────────────┘
```

### Color Scheme
**Dark Mode (Default):**
- Background: #0F172A (Deep midnight)
- Surface: #1E293B (Dark slate)
- Primary: #8B5CF6 (Violet)
- Text: #F1F5F9 (Off-white)

**Light Mode:**
- Background: #FFFFFF
- Surface: #F8FAFC
- Primary: #6366F1 (Indigo)
- Text: #0F172A

### Onboarding Flow
1. Welcome screen with app introduction
2. Privacy explanation (local-only processing)
3. Journal storage location selection
4. Theme preference selection
5. Optional: Create first journal entry

## Development Plan & Current Progress

### Phase 1: Foundation (Week 1) - ✅ COMPLETED
- [x] Project setup with uv
- [x] Basic Flet application structure (main.py:646907 lines total)
- [x] Three-panel UI layout (Header, Calendar/Editor row, AI panel)
- [x] Violet/indigo theme implementation (comprehensive theme system)
- [ ] Onboarding flow with directory selection ⚠️ PENDING

**Progress:** 80% complete - Missing onboarding flow

### Phase 2: Core Functionality (Week 2) - 🔄 IN PROGRESS
- [ ] Markdown editor with live preview ⚠️ PENDING
- [ ] File-based storage system ⚠️ PENDING (storage/ module exists but empty)
- [ ] Calendar navigation with entry indicators ⚠️ PENDING
- [ ] Auto-save implementation ⚠️ PENDING
- [ ] CRUD operations for journal entries ⚠️ PENDING

**Progress:** 0% complete - All core functionality needs implementation

### Phase 3: AI Integration (Week 3) - ❌ NOT STARTED
- [ ] Qwen2.5-3B-Instruct model bundling (Q4_K_M quantized) ❌ NOT STARTED
- [ ] llama.cpp integration for optimized inference ❌ NOT STARTED
- [ ] Async model loading with progress indicators ❌ NOT STARTED
- [ ] Reflection generation system with caching ❌ NOT STARTED
- [ ] AI reflection panel UI with loading states ❌ NOT STARTED
- [ ] Optimized prompt engineering for emotional intelligence ❌ NOT STARTED

**Progress:** 0% complete - AI module exists but empty

### Phase 4: Polish & Packaging (Week 4) - ❌ NOT STARTED
- [ ] Performance optimization ❌ NOT STARTED
- [ ] Cross-platform testing ❌ NOT STARTED
- [ ] Standalone executable creation ❌ NOT STARTED
- [ ] Final UI/UX refinements ❌ NOT STARTED
- [ ] Installation package creation ❌ NOT STARTED

**Progress:** 0% complete - Too early for polish phase

## Key Decisions Made

### Package Management
- **Chosen:** uv (fast, modern Python package manager)
- **Rationale:** Speed, reliability, better dependency resolution

### AI Model Integration
- **Chosen:** Qwen2.5-3B-Instruct (Q4_K_M quantized)
- **Rationale:** Best emotional intelligence for journal reflection tasks
- **Optimization:** Quantization reduces size from 6GB to ~1.9GB
- **Trade-off:** Moderate download size vs. high-quality psychological insights

### Storage Approach
- **Chosen:** User-selected local directory with markdown files
- **Rationale:** Portable, readable format; user controls data location
- **Benefits:** No vendor lock-in, easy backup/migration

### UI Framework
- **Chosen:** Flet (Python-based cross-platform UI)
- **Rationale:** Python ecosystem compatibility, rapid development
- **Benefits:** Single codebase for all platforms

## Success Metrics (Future)

### User Adoption Goals
- 1,000 active users within 3 months of MVP release
- 10,000 active users within 6 months
- Cross-platform availability on release

### Technical Performance Goals
- App startup time < 3 seconds (model loads lazily on first AI request)
- AI reflection generation ~9.5 seconds (meets <10 second target)
- Auto-save without user-visible lag (debounced to 30-second intervals)
- Memory usage ~2.1GB during AI processing (slightly above original 2GB target for quality)

### Business Model (Future)
- Freemium model: Free core features
- Pro features: Advanced AI insights, themes, statistics
- Pricing: $4.99/month or $39/year for Pro

## Current Status Summary

**Overall Progress: 20% Complete**

### ✅ What's Working:
- Complete theme system with dark/light mode switching
- Three-panel UI layout foundation (Header, Calendar+Editor, AI panel)
- Project structure and dependency management with uv
- Basic Flet application shell

### 🔄 Currently Implemented:
- `main.py` (221 lines): Main application class with layout
- `ui/theme.py` (394 lines): Comprehensive theme management system
- `pyproject.toml`: Dependencies and build configuration
- Empty module scaffolding for storage/, ai/, config/, ui/components/

### ❌ Critical Missing Components:
1. **Storage System**: No file I/O implementation
2. **Calendar Component**: No date navigation or entry indicators
3. **Markdown Editor**: No text editing functionality
4. **AI Integration**: No model loading or inference
5. **Onboarding Flow**: No directory selection or setup

### 📊 Code Statistics:
- **Total Lines**: 646,907 (includes dependencies)
- **Source Files**: 8 Python files
- **Main Implementation**: ~615 lines across main.py and theme.py
- **Test Coverage**: No tests implemented yet

## Next Steps (Priority Order)

### 🚨 Immediate (Phase 1 Completion):
1. **Onboarding Flow**: Directory selection and initial setup
2. **Calendar Component**: Date picker with entry indicators

### 🔥 Phase 2 Critical Path:
1. **Storage System**: File-based journal entry management
2. **Markdown Editor**: Text editing with live preview
3. **Calendar Navigation**: Integration with storage system
4. **Auto-save**: Prevent data loss

### 📈 Success Metrics for Next Sprint:
- [ ] User can select storage directory
- [ ] User can create/edit journal entries
- [ ] Calendar shows dates with existing entries
- [ ] Entries persist between app sessions

## Notes & Assumptions

- **Model Quality:** Qwen2.5-3B provides superior emotional intelligence (4.6/5 rating) for journal reflection
- **Performance:** Q4_K_M quantization maintains 97% quality while reducing size by 60%
- **Privacy Priority:** Users strongly prefer local processing over cloud-based features
- **Storage:** SQLite indexing enables efficient scaling to thousands of entries
- **Hardware:** 2.1GB RAM requirement is acceptable for quality improvement
- **Cross-platform:** llama.cpp ensures consistent performance across all platforms
- **UI Framework:** Flet supports required components for MVP scope

## Model Selection Summary

**Qwen2.5-3B-Instruct Selected Based On:**
- **Emotional Intelligence:** 4.6/5 rating for psychological insights and empathy
- **Performance:** 9.5 second generation time meets target
- **Efficiency:** Q4_K_M quantization reduces size from 6GB to 1.9GB
- **License:** Apache 2.0 allows commercial use
- **Quality:** Significantly better than smaller models for therapeutic-quality responses

*Detailed model analysis available in LLM_ANALYSIS.md*