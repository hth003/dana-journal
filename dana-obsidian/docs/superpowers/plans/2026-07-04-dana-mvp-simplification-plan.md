# Dana Obsidian MVP Simplification — Mode-Aware Reflection Plan (rev 2)

**Date:** 2026-07-04
**Branch:** feature/obsidian-plugin
**Source:** /plan-ceo-review (SCOPE REDUCTION mode) against user feedback, revised after
adversarial outside-voice review verified the plan against the code.
**Companion docs:** [../../prd.md](../../prd.md), [2026-07-04-dana-reflection-depth-plan.md](./2026-07-04-dana-reflection-depth-plan.md)

## Problem (from user feedback)

1. The four idle-screen options are indistinguishable — all of them run the same
   reflection over the same context (recent entries + active note).
2. "Reflect on today" is not grounded in the currently open note. The prompt
   explicitly asks for cross-entry patterns, so the response references other days.
3. The first response has no structure. Users want the insights + questions shape
   (see `dana-desktop/src/ai/prompts.py:65-73`) on the first response, then free chat.
4. Users want fewer, clearer options.

Root cause: there is no concept of a reflection *mode*. `DanaPanel.reflect()` →
`ContextResolver.resolve()` always builds one context (N recent entries by mtime,
active note appended) regardless of which button was pressed.

Additional defects confirmed in review (Claude review + independent outside-voice
pass over the code):

5. **Follow-up context loss.** The context-rich first API message is never stored in
   `this.messages` (`src/DanaPanel.ts:325-339`), so from turn 2 onward the model
   receives no journal content at all.
6. **Silent truncation via `max_tokens`.** `OpenAIProvider` hardcodes
   `max_tokens: 600` and never checks `finish_reason` (`src/providers/OpenAIProvider.ts:26`).
   A capped response ends "cleanly" and is saved as complete — the likely cause of
   the mid-sentence cutoff in the user's screenshot.
7. **Broken abort classification.** `abort('timeout')` rejects with the *string*
   `'timeout'`, not an Error, so `err instanceof Error` is false
   (`src/DanaPanel.ts:368`) and partials are discarded into ERROR_TIMEOUT instead
   of being handled per the intended timeout branch.
8. **No markdown rendering.** Responses are set via `textContent`
   (`src/DanaPanel.ts:170,194`) — any structured markdown would display as raw `**`.
9. **ConversationStore corrupts multi-paragraph messages.** `parseMarkdown` splits
   on `\n\n` and drops blocks not starting with a speaker tag
   (`src/ConversationStore.ts:63-74`); `save` overwrites the day file with only the
   current in-memory messages.
10. **Command palette bypasses all gating.** `dana-reflect-today` calls
    `panel.reflect()` unconditionally and `dana-how-have-i-been` injects a chip
    prompt (`main.ts:27-37`).

## Decisions (locked with user)

| Decision | Choice |
|----------|--------|
| Approach | A — mode-aware rewire, no retrieval/RAG in this pass |
| Options | **2 buttons**: "Reflect on this entry" + "Reflect on my week". Standalone vault-wide free-chat entry point deferred to v1.1 (TODOS.md) |
| Button semantics | **"Reflect on this entry"** — reflects on the open journal note, whatever its date, and says so ("the note you have open"). No today's-date check |
| Entry mode, no journal note open | Button **disabled** with subtitle "open a journal note first" — never falls back to another note |
| First-response structure | Structured **markdown**: 2-3 sentence reflection → `**Worth noticing:**` 2-3 bullets → one closing question. Follow-up turns are free conversation (the reply box — which already is free chat within a grounded session — stays) |
| Context placement | Resolved **once per conversation** and cached; injected into the **system prompt on every turn**. Never re-resolved mid-conversation |
| Old chips | Removed |

## Core design: conversation-scoped context

One decision resolves findings 5, 6-of-review (mid-chat note switch), and the
context-placement question in a single move:

```
IDLE ──[button/command, mode]──▶ startConversation(mode)
                                    │ resolve context ONCE:
                                    │   entry: [active journal note]
                                    │   week:  last N entries by date
                                    │ PIN { mode, paths[], snapshot[] } on panel
                                    ▼
                             every turn:
                               re-read pinned paths (cachedRead — the user
                               edits notes mid-conversation; Dana must see
                               the current text, not a stale quote)
                               file missing/deleted → fall back to its
                               turn-1 snapshot, never crash the thread
                               system prompt = persona(mode) + current entries
                             user/dana turns stay clean in this.messages
                                    │
        sendMessage() ──────────────┘   (WHICH files are context is pinned;
                                         switching notes mid-chat cannot
                                         kill or retarget the thread)
```

Mode + pinned paths survive a panel reload via frontmatter in the conversation
file (see Task 5).

## Tasks

### Task 1: `ReflectionMode` through the context path

- `src/types.ts`: `export type ReflectionMode = 'entry' | 'week';`
- `src/ContextResolver.ts`: `resolve(mode, activeFile, frontmatter, settings)`
  - `entry`: return **only** the active note via `readActiveFile`. Empty if the
    active note isn't a journal note (UI/commands gate this, but resolve stays safe).
  - `week`: last `maxContextEntries` entries **sorted by parsed filename date**
    (`YYYY-MM-DD`); files without a parseable date sort by mtime timestamp on the
    same ms scale. Oldest → newest. Active-note dedup kept.
- `src/VaultReader.ts`: date-aware sort; entry `date` label uses the parsed date,
  falling back to basename.

### Task 2: Mode-aware prompts with structured first response

- `src/PromptBuilder.ts`:
  - `buildSystemPrompt(mode, entries)` — persona + the cached entries + mode-scoped
    rules. The current hardcoded cross-entry instructions (`src/PromptBuilder.ts:6-9`)
    move into the `week` branch only; `entry` mode forbids referencing content not
    in the single provided note.
  - `buildFirstTurnInstruction(mode)` — the structured-markdown shape ported from
    `dana-desktop/src/ai/prompts.py`: brief reflection grounded in quoted specifics
    → `**Worth noticing:**` (2-3 insights: feeling/situation, external
    influences & relationships, an unaddressed topic) → exactly one open question.
    Applied on turn 1 only; follow-ups get the conversational persona rules.
  - User turns carry only user text — no entries duplicated outside the system prompt.
- Banned-words rule from the existing plan still applies.

### Task 3: Truncation + abort correctness

- `src/providers/OpenAIProvider.ts`: `max_tokens: 1024`; parse `finish_reason`
  from the stream — if `length`, surface a truncation flag to the caller.
- `src/providers/OllamaProvider.ts`: same for `done_reason === 'length'`.
- `src/providers/OllamaProvider.ts` **[P1 from eng review]**: NDJSON lines split
  across network reads are silently dropped (`generate()` decodes and splits
  each read independently; both halves of a straddling JSON object fail parse
  and hit the skip-catch — words go missing mid-response). Fix: carry a line
  buffer across reads; only parse complete lines; flush on `done`.
- `src/DanaPanel.ts`: classify aborts via `signal.aborted` + `signal.reason`
  (handles string rejection reasons — fixes finding 7); replace the single 30s
  whole-call timer with 30s time-to-first-token + 60s inter-token idle timeout.
- Any truncated/cut response renders a visible "Response was cut off" marker on
  the message (no separate Continue button in MVP; Retry already exists).

### Task 4: Markdown rendering

- `src/DanaPanel.ts`: stream as plain text (unchanged feel), then on completion
  render the message with Obsidian's `MarkdownRenderer.render()`; stored/reloaded
  messages render as markdown in `renderThread`.
- Pass the `DanaPanel` itself as the `Component` argument (`ItemView` extends
  `Component`) and the conversation file path as `sourcePath` so render children
  are cleaned up with the view — no leaked components.

### Task 5: ConversationStore v2

- Format: YAML frontmatter (`mode`, `date`, `contextPaths`, format version) +
  messages delimited by HTML-comment lines:
  `<!-- dana:msg role=dana -->` / `<!-- dana:msg role=user -->`.
  Invisible in Obsidian's reading view, zero collision with any user-typed
  markdown (users hand-edit these files by design), trivial to parse, and
  multi-paragraph structured responses survive round-trips (fixes finding 9).
- **[P1 from eng review]** File date key must use **local time**, not
  `toISOString()` (current `todayISO()` files a Californian's 8pm conversation
  under tomorrow's date). Additionally, the file is keyed to the
  **conversation-start date** stored in frontmatter — a conversation spanning
  midnight keeps writing to the file it started in.
- Day file holds **all** of the day's sessions separated by
  `<!-- dana:session -->` markers; "Start fresh" begins a new session block
  instead of overwriting earlier ones. Panel displays the latest session;
  `save` rewrites the file from the full day's sessions.
- Reload: `onOpen` restores the latest session, its `mode`, and its pinned
  `contextPaths` (content re-read fresh per the core design).
- Legacy files (v1 format, no frontmatter): parsed best-effort as a single
  session in `week` mode; never crash.

### Task 6: Two-button idle UI + command parity

- `renderIdle()`: two buttons with subtitle microcopy:
  - **Reflect on this entry** — "the note you have open" (disabled + "open a
    journal note first" when `!activeIsJournalNote`)
  - **Reflect on my week** — "your last N entries" using
    `settings.maxContextEntries`, not a hardcoded 7
  - Remove the three chips.
- Short active note (< 50 chars) in entry mode: dedicated copy — "Write a few more
  lines and I'll reflect with you." (new state or reuse EMPTY_NOTES with
  mode-aware copy).
- `main.ts`: `dana-reflect-today` → `dana-reflect-entry`, gated identically to
  the button (Notice "Open a journal note first" when not applicable); add
  `dana-reflect-week`; **remove** `dana-how-have-i-been`.
- `styles.css`: disabled-button + subtitle styles.

### Task 7: Observability

- One `console.debug` per conversation start and per turn: mode, entry count,
  total context chars, provider name, finish reason.

### Task 8: design.md sync

`docs/design.md` claims "implementers should not have to invent any UX
decisions" but still specs the old UI. Update in the same PR:

- IDLE wireframe → 2-button layout below (chips removed).
- Quick-prompt chips section → deleted.
- Entry points → commands become "Dana: Reflect on this entry",
  "Dana: Reflect on my week", "Dana: Open panel".
- Conversation persistence → v2 format (frontmatter + `<!-- dana:msg -->`
  comment delimiters, `<!-- dana:session -->` separators).
- DONE-state wireframe → structured response card (below).
- Footer copy → "Reading your last N entries" driven by
  `settings.maxContextEntries` (never a hardcoded 7).

### Tests (Jest, existing harness)

- ContextResolver: entry = active only; entry + non-journal = empty; week =
  date-sorted with mtime fallback, dedup.
- PromptBuilder: mode-scoped system prompts; first-turn-only structure
  instruction; single-entry week fallback intact.
- VaultReader: date sort with mixed parseable/unparseable filenames.
- ConversationStore: v2 round-trip preserves multi-paragraph structured messages;
  multi-session day file; legacy v1 parse.
- Message assembly: extract the per-turn API-payload construction into a pure
  helper (testable without the skeletal obsidian mock) and assert turn-2+
  payloads contain journal context in the system prompt.
- Providers: finish_reason/done_reason `length` sets the truncation flag
  (mock fetch).
- Providers **(CRITICAL regression guard)**: OllamaProvider reassembles an
  NDJSON object split across two stream reads (mock fetch yielding the JSON in
  two halves) — guards the line-buffer fix.
- Providers: abort mid-stream with a string reason is classified correctly
  (no raw error state, partial handled per Task 3).
- ConversationStore: local-date filing (mock `Date` at UTC-8 evening — file
  keys to the local day, not tomorrow UTC).
- ConversationStore: user message containing the literal delimiter string
  `<!-- dana:msg role=user -->` round-trips without splitting.
- ContextResolver: `maxContextEntries = 1` boundary in week mode.
- Message assembly: turn-1 with `userInput` (command-palette week + prompt path).
- Context re-read: pinned file edited between turns → turn-2 payload contains
  the updated text; pinned file deleted → snapshot fallback used, no throw.

## Design specifications (from /plan-design-review)

### IDLE state (2-button)

```
┌─────────────────────────────┐
│ ◉ Dana              [gear] │
│ ───────────────────────────│
│  How's the day going       │  ← time-aware greeting (journal note open)
│  so far?                   │     OR passive copy (no journal note)
│                             │
│  ┌─────────────────────┐   │
│  │ Reflect on this     │   │  ← primary, terracotta (--dana-primary)
│  │ entry               │   │
│  │ the note you have   │   │  ← subtitle: --text-muted, 0.85em,
│  │ open                │   │     separate span, not in accessible name
│  └─────────────────────┘   │
│  ┌─────────────────────┐   │
│  │ Reflect on my week  │   │  ← secondary/outline
│  │ your last 7 entries │   │  ← "7" = settings.maxContextEntries
│  └─────────────────────┘   │
└─────────────────────────────┘
```

- Disabled entry button (no journal note open): `opacity: 0.5`,
  `cursor: not-allowed`, subtitle swaps to "open a journal note first",
  `aria-disabled="true"` + `aria-describedby` → the subtitle span.
- At 240px panel width subtitles wrap to max 2 lines; never truncate the
  disabled-state explanation.

### Structured response card (first response of a conversation)

Visual hierarchy inside the existing warm card (`--dana-response-bg`):

1. Reflection prose — `--dana-font-response`, normal weight (read first)
2. `**Worth noticing:**` — bold inline label, NOT a heading; **fixed ritual
   wording, byte-identical every reflection** (testable contract with the
   model; journaling thrives on ritual)
3. 2-3 bullets — standard markdown list, 0.95em
4. Closing question — italic, its own paragraph (matches existing
   DONE-state convention)

Rendered via `MarkdownRenderer.render()` on completion; streaming shows plain
text with cursor, then formats in one swap (the visual "pop" is accepted —
no per-token markdown re-parse). The swap must not re-announce: container
keeps `aria-live="polite"`, render happens in place.

### Cut-off marker

One muted italic line inside the card, below the response text:
`Response was cut off · [Retry]`. Inside the card so it cannot be read as
Dana's voice; `--text-muted`; Retry is a text button.

### Mode-aware loading copy

- entry: "Dana is reading this note..."
- week: "Dana is reading your recent notes..."

### Short-note state (entry mode, < 50 chars)

Card copy: "Write a few more lines and I'll reflect with you." — [Dismiss]
ghost button. Warm, no error styling.

### Release note

One line in the release/changelog for updating users: "Dana got simpler:
two clear reflections — this entry, or your week." No in-app announcement
(subtraction default; it would be noise after day one).

### Test addition (design contract)

- PromptBuilder/e2e prompt tests assert the literal string
  `**Worth noticing:**` is requested in first-turn instructions, and the
  rendered first response is checked for the label in provider mocks.

## NOT in scope (deferred, with rationale)

- **Standalone vault-wide free-chat entry point (retrieval/RAG)** → v1.1, tracked
  in TODOS.md. The in-conversation reply box already provides free chat within a
  grounded session and stays.
- **Transformers.js zero-setup local provider** — still absent despite being PRD
  MVP scope; separate XL project. PRD honesty correction raised and explicitly
  skipped by the user in this review.
- **JSON-schema insight cards** — small local models mangle strict JSON; markdown
  structure delivers the same user value.
- **Daily-note creation flow** ("Open today's entry →") — template/filename logic;
  revisit after MVP feedback.
- **Today's-date strictness** — button renamed to "Reflect on this entry" instead;
  reflecting on an old open entry is a feature, honestly labeled.
- Pattern Cards, templates, mood viz, mobile — unchanged PRD non-goals.

## What already exists (reused)

- `ContextResolver` + structural interfaces (extend, don't rebuild)
- `VaultReader` truncation/sanitization; `JournalDetector`; `SecretStore`
- Single-entry prompt fallback in `PromptBuilder`
- Error states (`ERROR_NO_NOTES`, `EMPTY_NOTES`, `ERROR_NO_AI`) and retry flow
- Jest harness with obsidian mock (extended, not rebuilt)

## Failure Modes Registry

| Codepath | Failure | Rescued? | Test? | User sees | Logged |
|----------|---------|----------|-------|-----------|--------|
| provider stream | `max_tokens`/length stop | Y (T3) | Y | "cut off" marker + Retry | Y |
| provider stream | TTFT/idle timeout | Y (T3) | Y | "cut off" marker + Retry | Y |
| abort plumbing | string rejection reason | Y (T3) | Y | correct state, never a raw 500-style error | Y |
| turn 2+ | context missing | Y (design) | Y | grounded follow-ups | Y |
| mid-chat note switch (entry mode) | context re-resolve returns empty | Y (cached context) | Y | conversation continues | Y |
| entry mode, short note | entry rejected (<50 chars) | Y (T6) | Y | "Write a few more lines…" | Y |
| week, 1 entry | fake-pattern risk | Y (fallback) | Y | single-entry reflection | Y |
| week, 0 entries | no notes | Y (exists) | Y | folder check prompt | Y |
| reload | legacy v1 conversation file | Y (T5) | Y | best-effort restore | Y |
| command palette | entry command, no journal note | Y (T6) | Y | Notice, no wrong grounding | Y |
| ollama stream | NDJSON split across reads | Y (T3) | Y | complete responses, no dropped words | Y |
| store filing | UTC date drift (evening, UTC-negative) | Y (T5) | Y | conversation under the right local day | Y |
| mid-chat | pinned note edited | Y (design) | Y | Dana quotes current text | Y |
| mid-chat | pinned note deleted | Y (design) | Y | snapshot fallback, thread survives | Y |

## Success criteria

- "Reflect on this entry" quotes only the open note — verifiable by a user in one
  try. This is the trust repair.
- First response always renders the reflection → **Worth noticing:** bullets →
  question shape, as formatted markdown (no raw `**`).
- A 5-turn conversation still references journal specifics on turn 5, and survives
  the user switching notes mid-chat.
- No response is ever silently truncated — cap hits and timeouts are visibly marked.
- Reopening the panel restores the conversation with its structure intact.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 1 | CLEAR | mode: SCOPE_REDUCTION, 0 critical gaps, 1 deferred to TODOS |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR | 4 issues (2 P1 bugs: Ollama NDJSON drop, UTC date drift), 0 critical gaps remaining |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | CLEAR | score: 6/10 → 9/10, 9 decisions |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **CROSS-MODEL:** Outside voice (Claude subagent, fresh context) found 13 issues in rev 1; all HIGH/MED incorporated into rev 2, including overturning the truncation diagnosis (max_tokens cap, not the 30s timer).
- **ENG DECISIONS:** pin context paths + re-read content per turn (snapshot fallback); ConversationStore v2 uses HTML-comment delimiters; local-date file keys.
- **UNRESOLVED:** 0
- **VERDICT:** CEO + ENG + DESIGN CLEARED — ready to implement.
