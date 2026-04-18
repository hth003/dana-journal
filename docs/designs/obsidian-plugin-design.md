# Dana for Obsidian — UX Design Spec

**Version:** 1.0  
**Branch:** feature/obsidian-plugin  
**Date:** 2026-04-18  
**Companion to:** [obsidian-plugin-prd.md](./obsidian-plugin-prd.md)

This document is the complete UX specification. Every interaction state, copy string, layout rule, and design token is defined here. Implementers should not have to invent any UX decisions.

---

## Research: How Obsidian Users Journal

- Daily notes auto-open on Obsidian launch — users see them constantly
- Writing happens in bursts throughout the day, not dedicated "journaling sessions"
- Power users live in the command palette (Cmd+P) — the most native Obsidian trigger
- Templates that feel like homework kill spontaneity
- Anything that requires a separate "journaling mode" fails
- Users are allergic to plugins that modify note rendering

**Design principle from this:** Dana must be ambient. It lives in the ribbon and command palette. It never interrupts. The user triggers it; Dana doesn't impose itself.

---

## Information Hierarchy

**What the user sees, in order:**

In the Ribbon (always visible):
- Small Dana leaf icon (terracotta #E07A5F) in Obsidian's left ribbon
- Click → opens/closes Dana sidebar panel

In the Sidebar Panel:
1. Dana header (avatar + name) — identity anchor
2. Current state content (idle prompt / loading / response)
3. Action buttons — contextual to state
4. Settings gear icon — top right corner, small

Rules:
- The reflection text is the most important thing. It gets the most space.
- Dana's identity is secondary — small, present but not dominating.
- Action buttons are tertiary — visible but not competing.
- Settings are background — never surface unless user invokes them.

---

## Navigation Flow

```
RIBBON ICON (always visible)
        │
        ▼
DANA SIDEBAR PANEL
        │
   ┌────┴─────────────────────┐
   │                          │
IDLE STATE            first run → SETUP WIZARD
   │
   │ user clicks "Reflect on today"
   ▼
LOADING STATE (2-3s)
   │
   │ response ready
   ▼
STREAMING STATE (tokens appear)
   │
   │ complete
   ▼
DONE STATE
   │
   ├── user types reply → CONVERSATION STATE
   └── user clicks "Start fresh" → IDLE STATE
```

---

## Interaction States

All 10 states fully specified:

| State | What User Sees | Primary Action |
|-------|---------------|----------------|
| SETUP (1st run) | 3-step wizard: folder → AI mode → done | "Get started" |
| IDLE | Dana avatar + 3 quick-prompt chips + time-aware greeting | "Reflect on today" |
| LOADING | "Dana is reading your recent notes..." + animated dots | [Cancel] |
| STREAMING | Response text appearing token by token with cursor | [Stop] |
| DONE | Full reflection in warm card + text input | "Continue" / "Copy" |
| CONVERSATION | Chat thread (Dana, user, Dana...) | Text input + Send |
| ERROR-NO-AI | "Dana needs a brain" card | "Set up AI →" |
| ERROR-TIMEOUT | "Taking longer than usual..." | [Retry] [Cancel] |
| ERROR-NO-NOTES | "No journal notes found in [folder]" | "Change folder →" |
| EMPTY-NOTES | "Start writing and Dana will reflect" | [Dismiss] |
| DOWNLOADING | Progress bar + "Downloading Dana's brain (X MB of Y MB)" | [Cancel] |

### State coverage per feature

| Feature | Loading | Empty | Error | Success | Partial |
|---------|---------|-------|-------|---------|---------|
| Sidebar panel | Dots | Idle state | See error table | Streaming | — |
| Vault read | Dots | "No notes" | "Can't read" | Context set | — |
| AI generation | Dots | "No resp." | Timeout / no-AI | Streaming | Stop btn |
| Model download | Bar | — | Checksum fail | Done | Resume |
| Setup wizard | — | Step 1 | Folder invalid | Onboarded | Can skip |

---

## Wireframes

### IDLE STATE

```
┌─────────────────────────────┐
│ ◉ Dana              [gear] │  ← avatar + name + settings gear
│                             │
│ ─────────────────────────  │
│                             │
│  Good morning. What's on   │  ← time-aware greeting (see below)
│  your mind as the day      │
│  begins?                   │
│                             │
│  ┌─────────────────────┐   │
│  │  Reflect on today   │   │  ← primary CTA (terracotta bg)
│  └─────────────────────┘   │
│                             │
│  ┌──────────────────────┐  │
│  │ What's been on my    │  │  ← quick prompt chip (subtle)
│  │ mind?                │  │
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │ Process a feeling    │  │
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │ How have I been      │  │
│  │ lately?              │  │
│  └──────────────────────┘  │
│                             │
│ Reading 7 recent notes     │  ← muted text, bottom
└─────────────────────────────┘
```

### LOADING STATE

```
┌─────────────────────────────┐
│ ◉ Dana              [gear] │
│                             │
│  Dana is reading your      │
│  recent notes...           │
│                             │
│         • • •              │  ← animated dots (not a spinner)
│                             │
│  ┌─────────────────────┐   │
│  │       Cancel        │   │  ← secondary button
│  └─────────────────────┘   │
└─────────────────────────────┘
```

### DONE STATE

```
┌─────────────────────────────┐
│ ◉ Dana              [gear] │
│                             │
│ ┌─────────────────────────┐ │
│ │ I noticed you've written │ │  ← warm response card
│ │ about the project stress │ │     subtle terracotta tint bg
│ │ three times this week.   │ │
│ │                          │ │
│ │ What does it feel like   │ │  ← Dana's question (italic)
│ │ to sit with that right   │ │
│ │ now?                     │ │
│ └─────────────────────────┘ │
│                             │
│ ┌──────────────────────┐   │
│ │  Write a response... │   │  ← text input
│ └──────────────────────┘   │
│                             │
│ [Copy]        [Start fresh] │
└─────────────────────────────┘
```

### FIRST-RUN — Step 1 (folder)

```
┌─────────────────────────────┐
│         ◉ Dana              │  ← centered, larger avatar
│                             │
│       Meet Dana             │  ← h1
│  Your private journaling    │
│  companion.                 │
│                             │
│  — — Step 1 of 3 — —       │  ← step indicator
│                             │
│  Where are your journal     │
│  notes?                     │
│                             │
│  ┌──────────────────────┐  │
│  │ /Daily Notes         │  │  ← folder picker
│  └──────────────────────┘  │
│                             │
│  Your notes stay on your   │
│  device. Always.            │  ← reassurance, muted
│                             │
│  ┌─────────────────────┐   │
│  │       Next →        │   │  ← primary (terracotta)
│  └─────────────────────┘   │
│                             │
│       Skip for now          │  ← text link, muted
└─────────────────────────────┘
```

### FIRST-RUN — Step 2 (AI mode)

```
┌─────────────────────────────┐
│         ◉ Dana              │
│                             │
│  How should Dana think?     │  ← h1
│                             │
│  — — Step 2 of 3 — —       │
│                             │
│  ┌─────────────────────┐   │  ← LOCAL card (highlighted, default)
│  │  Local & Private    │   │
│  │  Runs on your       │   │
│  │  device. ~2GB.      │   │
│  │  Works offline.     │   │
│  │                     │   │
│  │  [Download now]     │   │
│  │  (free)             │   │
│  └─────────────────────┘   │
│                             │
│           or                │
│                             │
│  ┌─────────────────────┐   │  ← API card (smaller, secondary)
│  │  API Key            │   │
│  │  [sk-...        ]   │   │
│  │  OpenAI or Claude   │   │
│  └─────────────────────┘   │
│                             │
│       Skip for now          │
└─────────────────────────────┘
```

---

## Design Tokens

```css
/* Dana's brand colors — use only for accent elements */
--dana-primary: #E07A5F;                       /* terracotta */
--dana-secondary: #81B29A;                     /* sage green */
--dana-response-bg: rgba(224, 122, 95, 0.08); /* warm card tint */

/* Layout */
--dana-avatar-size: 28px;
--dana-spacing-sm: 8px;
--dana-spacing-md: 16px;
--dana-spacing-lg: 24px;

/* Always defer to Obsidian's own variables */
--dana-font-ui: var(--font-interface);
--dana-font-response: var(--font-text);
--dana-radius: var(--radius-m);  /* Obsidian's 8px standard */
```

Rules:
- Never override Obsidian's theme colors for backgrounds or body text
- Only use terracotta and sage for accent elements (buttons, active states, response card tint)
- Use Obsidian CSS variables (`--text-normal`, `--text-muted`, `--background-primary`) everywhere else
- Both light and dark Obsidian themes must work natively

---

## Copy & Voice

### Text that must NOT appear anywhere in the plugin

- "AI-powered journaling companion"
- "Leverage AI to gain insights"
- "Your mental wellness journey"
- "Unlock the power of reflection"
- "Robust", "comprehensive", "holistic"

### Time-aware idle prompts (rotate based on time of day)

| Time | Greeting |
|------|---------|
| 5am – 12pm | "Good morning. What's on your mind as the day begins?" |
| 12pm – 6pm | "How's the day going so far?" |
| 6pm – midnight | "How are you winding down?" |
| No recent entries | "Whenever you're ready to write, I'm here." |

### Quick prompt chips (always visible in IDLE)

- "What's been on my mind?"
- "Process a feeling"
- "How have I been lately?"

### Loading copy

- "Dana is reading your recent notes..."

### Error copy

| Error | Copy | Action |
|-------|------|--------|
| No AI configured | "Dana needs a brain to reflect with you." | "Set up AI →" |
| AI timeout | "Taking longer than usual. Still thinking..." | [Retry] [Cancel] |
| No notes found | "No journal notes found in [folder]. Is this the right folder?" | "Change folder →" |
| No notes yet | "Start writing, and Dana will reflect with you." | [Dismiss] |
| Checksum fail | "Something went wrong with the download. Let's try again." | [Retry] |

---

## Entry Points

Two only. No more.

1. **Ribbon icon** (always visible): click to toggle Dana panel open/closed
2. **Command palette**: three commands registered
   - "Dana: Reflect on today"
   - "Dana: How have I been lately?"
   - "Dana: Open panel"

Do NOT add any inline buttons inside the note editor. Obsidian users notice and dislike plugins that modify note rendering.

---

## First-Run Flow

3 steps, all skippable:

**Step 1 — Journal folder**
- Folder picker, defaults to vault root
- Reassurance text: "Your notes stay on your device. Always."
- "Skip for now" text link at bottom

**Step 2 — AI mode**
- Local AI card: large, highlighted, default selection — "Local & Private. Runs on your device. ~2GB. Works offline. [Download now] (free)"
- API key card: smaller, secondary — text field for OpenAI or Anthropic key
- "Skip for now" text link at bottom

**Step 3 — Done**
- "Dana is ready. Open a journal note and click the leaf icon in the ribbon."
- No confetti. No animation. Just calm and ready.

---

## Conversation Persistence

Dana remembers within a day. Users can read, edit, or delete the record.

Storage format:
- File path: `{journal-folder}/.dana/YYYY-MM-DD-conversation.md`
- Format: plain markdown, alternating `**Dana:**` and `**Me:**` blocks
- Dana reads the most recent conversation file on panel open for continuity

Example:
```markdown
**Dana:** I noticed you've written about the project stress three times this week. What does it feel like to sit with that right now?

**Me:** Honestly exhausting. I feel like I keep circling the same thing.

**Dana:** What would it mean to stop circling and just let it be unresolved for now?
```

---

## Daily Note Integration

### Default behavior (passive)

- User opens any note in the configured journal folder
- Dana panel, if open, silently reads the current note as context
- No auto-popup, no notification, no interruption
- User triggers reflection from ribbon or command palette

### Optional behavior (active, opt-in)

- After user writes for 5+ minutes in a journal note, Dana shows a toast notification: "Dana has a reflection ready — [open]"
- Toast auto-dismisses after 8 seconds
- Off by default, enabled in settings

### Daily note recognition logic

```
Is current note in configured journal folder?
  YES → Dana active (ribbon icon brighter)
  NO  → Dana passive (ribbon icon dim, panel shows: "Open a journal note to reflect")

Auto-detection priority (first match wins):
  1. Frontmatter has tag: journal or daily
  2. Filename matches YYYY-MM-DD.md
  3. Note is inside configured journal folder
```

---

## Responsive & Accessibility

### Panel width

| Width | Behavior |
|-------|---------|
| < 240px | Not supported (Obsidian minimum) |
| 240px | Hide avatar, show just name + content |
| 240–400px | Normal layout |
| > 400px | Max-width 400px, centered |

### Keyboard shortcuts

| Action | Key |
|--------|-----|
| Toggle Dana panel | Cmd+Shift+D (configurable) |
| Tab through panel | Standard tab order: avatar → chips → primary button → settings |
| Activate chip | Enter |
| Cancel / close | Escape (context-dependent: closes panel in idle, cancels generation during loading) |

### Touch targets

- All buttons: minimum 36px height
- Prompt chips: minimum 32px height, full-width preferred
- Settings gear: 28px × 28px

### Accessibility markup

```
Panel:        role="complementary", aria-label="Dana journaling companion"
Response area: role="status", aria-live="polite"
Loading state: aria-busy="true" on the panel
```

### Color contrast

- White text on terracotta button: 3.1:1 (meets AA for large text, 18px+)
- Body text: `var(--text-normal)` — always meets contrast in both Obsidian themes
- Muted text: `var(--text-muted)` — always meets contrast in both Obsidian themes

---

## Design Review Scores

| Pass | Dimension | Before | After |
|------|-----------|--------|-------|
| 1 | Information Architecture | 2/10 | 9/10 |
| 2 | Interaction State Coverage | 1/10 | 10/10 |
| 3 | User Journey & Emotional Arc | 2/10 | 9/10 |
| 4 | AI Slop Risk | 3/10 | 9/10 |
| 5 | Design System Alignment | 0/10 | 8/10 |
| 6 | Responsive & Accessibility | 1/10 | 8/10 |
| 7 | Unresolved Decisions | 1/10 | 9/10 |
| — | **Overall** | **3/10** | **9/10** |
