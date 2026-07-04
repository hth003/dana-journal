# Dana for Obsidian

A warm journaling companion that lives in your Obsidian sidebar. Dana reads your recent vault notes and reflects with you — through streaming AI responses, multi-turn conversation, and no interruptions to your writing flow.

[![Obsidian](https://img.shields.io/badge/Obsidian-1.4%2B-7c3aed.svg)](https://obsidian.md)
![Desktop only](https://img.shields.io/badge/platform-desktop%20only-lightgrey.svg)

> Dana for Obsidian is separate from [Dana Desktop](../dana-desktop/README.md). It uses your existing Obsidian vault and connects to Ollama or OpenAI for AI — no local model download required.

---

## Installation

### Community plugins (when published)

1. Open Obsidian Settings → Community plugins → Browse
2. Search "Dana"
3. Install and enable

### Manual install

1. Download `main.js`, `styles.css`, and `manifest.json` from GitHub Releases
2. Create `.obsidian/plugins/dana-journal/` in your vault
3. Copy the three files there
4. In Obsidian: Settings → Community plugins → enable Dana

### For development

```bash
cd dana-obsidian
npm install
npm run dev     # watch mode — copies output to vault if VAULT_PATH is set
```

---

## First-run setup

When you open the Dana panel for the first time, a 3-step wizard runs:

**Step 1 — Journal folder**
Pick the folder in your vault where you write journal notes. Leave empty to scan the whole vault. Your notes never leave your device.

**Step 2 — AI mode**
Choose how Dana thinks:
- **Ollama** (default): runs locally on your machine, completely private, free
- **OpenAI**: cloud API, requires an API key, uses GPT-4o-mini

**Step 3 — Done**
Dana is ready. Open a journal note and click the leaf icon in the ribbon.

---

## AI provider setup

### Ollama (local, recommended)

1. Install Ollama: [ollama.com](https://ollama.com)
2. Pull a model: `ollama pull llama3.2`
3. In Dana settings, set Host to `http://localhost:11434` (default) and Model to `llama3.2`
4. Click "Test connection" to verify

Ollama runs on your device — no API key, no data sent to a cloud.

### OpenAI

1. In Dana settings, select OpenAI as provider
2. Paste your API key (stored locally in Obsidian plugin data, never transmitted except to OpenAI)
3. Dana uses `gpt-4o-mini` with a 600-token response cap for cost efficiency

---

## Usage

**Open the panel**: Click the leaf icon (◉) in Obsidian's left ribbon, or use the command palette (Cmd+P → "Dana: Open panel").

**Get a reflection**: Click "Reflect on today" or one of the quick-prompt chips. Dana reads your recent journal notes, then streams a response.

**Continue the conversation**: Type a reply in the input at the bottom. Dana maintains context across the full conversation thread.

**Commands registered:**
- `Dana: Reflect on today`
- `Dana: How have I been lately?`
- `Dana: Open panel`

**Keyboard shortcut**: Cmd+Shift+D toggles the panel (configurable in Obsidian hotkeys).

---

## Features

### Streaming responses

Dana streams tokens in real time. You can stop mid-generation — partial responses are saved to the conversation file.

### Conversation memory

Each day's conversation is saved to `.dana/{YYYY-MM-DD}-conversation.md` inside your journal folder, in plain markdown:

```markdown
**Dana:** I noticed you've written about the project stress three times this week. What does it feel like to sit with that right now?

**Me:** Honestly exhausting. I feel like I keep circling the same thing.

**Dana:** What would it mean to stop circling and just let it be unresolved for now?
```

You can read, edit, or delete these files directly. Dana loads today's conversation on panel open for continuity.

### Time-aware greetings

| Time | Greeting |
|------|---------|
| 5am – 12pm | "Good morning. What's on your mind as the day begins?" |
| 12pm – 6pm | "How's the day going so far?" |
| 6pm – midnight | "How are you winding down?" |
| No recent entries | "Whenever you're ready to write, I'm here." |

### Quick-prompt chips

Three always-visible prompts in the IDLE state:
- "What's been on my mind?"
- "Process a feeling"
- "How have I been lately?"

### Prompt injection protection

Before any vault content is passed to an AI provider, VaultReader sanitizes it with 14 regex patterns — stripping YAML frontmatter, markdown syntax, wikilinks, and rejecting injection attempts (e.g. "ignore previous instructions", "system:", "forget all").

---

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Journal folder | (whole vault) | Folder Dana reads notes from |
| Max context entries | 7 | How many recent notes to include (3–30) |
| AI provider | Ollama | Ollama or OpenAI |
| Ollama host | `http://localhost:11434` | Ollama API endpoint |
| Ollama model | `llama3.2` | Model name to use |
| OpenAI API key | — | Stored in plugin data, masked in UI |

---

## Panel states

Dana's sidebar has 9 distinct states:

| State | What you see |
|-------|-------------|
| SETUP | First-run wizard |
| IDLE | Greeting + quick-prompt chips + "Reflect on today" button |
| LOADING | "Dana is reading your recent notes..." + animated dots |
| STREAMING | Response appearing token by token |
| DONE | Full response + text input |
| CONVERSATION | Full chat thread + input |
| ERROR_NO_AI | "Dana needs a brain" + setup link |
| ERROR_TIMEOUT | 30-second timeout reached + retry |
| ERROR_NO_NOTES | No notes found in configured folder |

---

## Development

### Commands

```bash
npm install          # Install dependencies
npm run dev          # Development build (watch mode)
npm run build        # TypeScript check + production build
npm test             # Run Jest test suite
```

### Output files

`npm run build` produces two files that make up the plugin:
- `main.js` — compiled TypeScript
- `styles.css` — plugin styles (copy directly, no build step needed)

### Architecture

```
src/
├── DanaPanel.ts          Main ItemView panel — 9-state machine, all UI rendering
├── VaultReader.ts        Read vault files + sanitize content for prompts
├── ConversationStore.ts  Load/save .dana/{date}-conversation.md
├── PromptBuilder.ts      Build system prompt + user messages
├── JournalDetector.ts    Detect which notes are journal entries
├── SettingsTab.ts        Plugin settings UI
├── types.ts              TypeScript interfaces
└── providers/
    ├── AIProvider.ts     Abstract interface: generate() → AsyncGenerator<string>
    ├── OllamaProvider.ts Ollama HTTP streaming (JSON lines from /api/chat)
    └── OpenAIProvider.ts OpenAI SSE streaming (/v1/chat/completions)
```

**State flow:**
```
SETUP → IDLE
          ↓ user triggers reflection
        LOADING → STREAMING → DONE → CONVERSATION
                       ↓
                  ERROR_TIMEOUT / ERROR_NO_AI / ERROR_NO_NOTES
```

**Provider interface:**
```typescript
interface AIProvider {
  generate(messages: ChatMessage[], signal: AbortSignal): AsyncGenerator<string>
  isAvailable(): Promise<boolean>
}
```

Both `OllamaProvider` and `OpenAIProvider` implement this. Provider selection: preferred provider → first available (Ollama then OpenAI) → ERROR_NO_AI.

**VaultReader sanitization** strips: YAML frontmatter, headers, wikilinks, external links, images, bold/italic, code blocks. Then truncates each entry to 50–2000 characters at a sentence boundary.

**PromptBuilder persona:** Dana gives 2–4 sentence reflections, references specific content, ends with one open question. Warm companion tone. Banned words: "journey", "mindfulness", "wellness", "AI".

### Tests

```bash
npm test
```

Jest + ts-jest. Test files in `tests/`:
- `VaultReader.test.ts` — sanitization, truncation, frontmatter stripping
- `JournalDetector.test.ts` — note detection logic
- `PromptBuilder.test.ts` — prompt assembly

### Design docs

- [`docs/design.md`](./docs/design.md) — complete UX spec (states, wireframes, copy, accessibility)
- [`docs/prd.md`](./docs/prd.md) — product requirements

### Design tokens

```css
--dana-primary: #E07A5F;                       /* terracotta — buttons, active states */
--dana-secondary: #81B29A;                     /* sage green — highlights */
--dana-response-bg: rgba(224, 122, 95, 0.08); /* warm tint on response cards */
```

All other colors defer to Obsidian's own CSS variables (`--text-normal`, `--background-primary`, etc.). Both light and dark Obsidian themes work without any special handling.

---

## Privacy

- Vault content is sanitized before being sent to any AI provider
- With Ollama: nothing leaves your machine
- With OpenAI: only the sanitized, truncated note content (not raw files) is sent
- Conversation files are plain markdown stored inside your vault — you own them
- No analytics, no crash reporting, no external requests beyond the AI provider you configured
