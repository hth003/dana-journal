# Dana for Obsidian — Product Requirements Document

**Version:** 1.0 MVP  
**Branch:** feature/obsidian-plugin  
**Date:** 2026-04-18

## One-line

A warm AI journaling companion that lives inside your Obsidian vault, knows your writing history, and surfaces emotional patterns without sending your data anywhere.

## Problem

Obsidian users journal regularly but have no structured way to extract emotional insight from their notes. ChatCBT (the closest competitor, 5,872 downloads) offers reactive CBT chat but ignores the vault entirely — every session starts blank. It's a better notepad widget, not a companion that grows with you.

## Target User

Obsidian power users (developers, writers, knowledge workers) who already journal but want reflective depth without a therapy app or cloud AI dependency.

## Jobs To Be Done

1. "Help me process what I'm feeling right now" → reflective conversation with vault context
2. "What have I been struggling with lately?" → cross-entry pattern awareness
3. A private, zero-setup companion that doesn't need an API key

## Competitive Advantages Over ChatCBT

| Dimension | ChatCBT | Dana for Obsidian |
|-----------|---------|-------------------|
| Vault awareness | None (blank slate each session) | Reads recent journal entries for context |
| AI persona | Generic CBT bot | Named companion (Dana) with warm, non-clinical voice |
| Local AI | Requires Ollama setup | Transformers.js — zero setup, works offline |
| Reflection style | Reactive only | Context-aware prompts based on recent entries |
| Last active | 10 months stale | Active development |
| Psychology | CBT only | Broader emotional intelligence |

## MVP Features (v1)

### 1. Dana Sidebar Panel
- Obsidian leaf/panel (right sidebar)
- Manual trigger: "Ask Dana" button — NOT auto on every note open
- Streaming text output (token by token, feels alive)
- Regenerate + copy buttons

### 2. Vault-Aware Reflection
- Reads last 7 journal entries (configurable: 3/7/14/30 days)
- Truncate entries to 2,000 chars each to manage context size
- Folder setting: user specifies journal folder
- Graceful fallback if no entries found

### 3. Local-First AI (Transformers.js)
- Default: Phi-3-mini or Qwen2.5-1.5B via Transformers.js (WASM, ~2GB)
- Download on first use with progress bar
- Resume interrupted downloads
- SHA256 checksum verification
- Fallback options: Ollama (localhost), OpenAI API, Anthropic API

### 4. Companion Voice
- Port prompt engineering from `src/ai/prompts.py`
- Warm, non-clinical tone
- Asks questions rather than giving advice
- Does not claim to be a therapist

## Non-Goals (v1)

- Pattern Cards / weekly summary → v1.1
- Journal Templates → v1.1
- Mood visualization → v2
- Mobile support → v2 (Obsidian mobile has plugin restrictions)
- Multi-vault → v2

## Technical Architecture

### Stack
- TypeScript + Obsidian Plugin SDK
- React for sidebar UI (Obsidian uses React internally)
- Transformers.js for local AI inference
- Hugging Face Hub JS for model download

### Key Constraints
- MAX_ENTRY_CHARS = 2000 per entry
- MAX_CONTEXT_ENTRIES = 7
- AI generation timeout = 30s
- API keys stored in OS keychain, NOT in data.json (Obsidian Sync safety)

### AIProvider Interface (strategy pattern)
```typescript
interface AIProvider {
  generate(prompt: string, context: string): AsyncGenerator<string>;
  isAvailable(): Promise<boolean>;
}
// Implementations: TransformersJSProvider, OllamaProvider, OpenAIProvider
```

## Distribution

- Obsidian Community Plugin registry (PR to obsidian-releases repo)
- Model hosted on Hugging Face Hub
- Free, open source
- Future: Dana Pro tier ($4/month) for cloud AI + advanced features

## Success Metrics (30 days post-launch)

- 1,000 downloads
- 4.5+ star rating in Obsidian plugin directory
- Exceed ChatCBT monthly download rate

## Security Notes

- API keys: OS keychain only, never data.json
- Prompt injection: sanitize vault content before inserting into AI context
- Cloud AI: only activated when user explicitly configures an API key

## Known Deferred Items

- Pattern Cards: weekly summary of recurring themes
- Journal Templates: daily check-in, difficult emotion, weekly review
- Mobile: Obsidian mobile plugin restrictions to evaluate
- Pro tier: Stripe integration, cloud AI

## Design Spec

Full UX specification (wireframes, all 10 interaction states, design tokens, copy, accessibility) is in [obsidian-plugin-design.md](./obsidian-plugin-design.md).

Key decisions captured there:

**Entry points:** Ribbon icon + command palette only. No inline editor buttons.

**Conversation persistence:** `{journal-folder}/.dana/YYYY-MM-DD-conversation.md` — plain markdown the user can read and edit.

**Time-aware idle prompts:**
- Morning (5am–12pm): "Good morning. What's on your mind as the day begins?"
- Afternoon (12pm–6pm): "How's the day going so far?"
- Evening (6pm–midnight): "How are you winding down?"
- No recent entries: "Whenever you're ready to write, I'm here."

**First-run:** 3 steps, all skippable — journal folder → AI mode → done.

**Daily note detection priority:** frontmatter tags → YYYY-MM-DD filename → folder config.

**Design tokens:**
```css
--dana-primary: #E07A5F;
--dana-secondary: #81B29A;
--dana-response-bg: rgba(224, 122, 95, 0.08);
```
