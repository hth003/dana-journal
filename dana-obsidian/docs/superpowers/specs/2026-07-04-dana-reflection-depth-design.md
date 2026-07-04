# Dana for Obsidian — Fix Reflection Depth & API Key Storage

**Date:** 2026-07-04
**Branch:** feature/obsidian-plugin
**Companion to:** [../prd.md](../prd.md), [../design.md](../design.md)

## Problem

A code review against the PRD/design spec found that several MVP features described as implemented are not actually wired up, and one security requirement is violated outright:

1. **Vault-aware reflection is dead code.** `VaultReader.readRecentEntries()` reads the last N configured journal entries and is fully unit-tested, but `DanaPanel.reflect()` never calls it — every reflection (including the "How have I been lately?" command, whose entire purpose is cross-entry pattern awareness) only reads the single currently active file via `readActiveFile()`. The IDLE screen even says "Reading 7 recent notes" while reading exactly one. This is the direct cause of the shallow, single-day-recap reflections reported by the user.
2. **`JournalDetector` is fully implemented, tested, and never imported anywhere** outside its own test file. Dana has no concept of whether the active note is actually a journal entry, so it will "reflect" on any open file, and the design spec's passive/active ribbon behavior doesn't exist.
3. **OpenAI API keys are stored in plaintext** in the plugin's `data.json`, confirmed by the settings UI's own description text. The PRD explicitly requires OS keychain storage to avoid leaking keys via Obsidian Sync.
4. The prompt sent to the AI doesn't ask for cross-entry synthesis even when given multiple entries — it asks for "a brief reflection ... based on these entries," which produces a recap of the most salient one rather than naming a recurring pattern.

**Explicitly out of scope for this pass:** a Transformers.js local-AI provider (PRD's "zero setup" competitive differentiator). This is missing entirely today but is a much larger, separate project (bundling a ~2GB WASM model, download/resume/checksum UX). Flagged as a follow-up doc correction: the PRD currently describes this as shipped MVP scope when it isn't.

## Goals

- Dana's reflections draw on multiple recent journal entries, weighted toward the currently open note when it is itself a journal entry.
- Dana knows whether the active note is a journal entry and reflects that in the ribbon icon and idle-state copy.
- The prompt explicitly asks the model to synthesize a recurring thread across entries, not recap the most recent one.
- OpenAI API keys are encrypted at rest using OS-backed encryption instead of stored in plaintext.

## Non-goals

- Transformers.js / local WASM inference provider.
- Mobile support (already a stated PRD non-goal).
- The optional "5 minutes idle → toast" nudge from the design spec (not part of the reported issues; can be picked up separately).

## Architecture

### New unit: `ContextResolver`

The bug exists because the decision of "what journal content counts as context" currently lives inside `DanaPanel`, an `ItemView` — a rendering class, not a testable unit. Extract that decision into its own class, alongside the existing `VaultReader` and `JournalDetector`:

```typescript
interface ResolvedContext {
  entries: JournalEntry[];      // recent entries, deduped, ordered oldest → newest
  activeIsJournalNote: boolean; // drives ribbon state + idle copy
}

class ContextResolver {
  constructor(private vaultReader: VaultReader, private journalDetector: JournalDetector) {}

  async resolve(
    activeFile: TFile | null,
    frontmatter: Record<string, unknown> | null,
    settings: DanaSettings
  ): Promise<ResolvedContext>
}
```

Logic:
1. Read `settings.maxContextEntries` recent entries from `settings.journalFolder` via the existing `VaultReader.readRecentEntries()`.
2. Determine `activeIsJournalNote` via `JournalDetector.isJournalNote(activeFile, settings.journalFolder, frontmatter)`.
3. If the active file is a journal note and its path isn't already in the recent-entries list, read it via `VaultReader.readActiveFile()` and append it as the most recent/most-weighted entry.
4. If the active file is not a journal note, or there is none, return the recent entries alone.

`DanaPanel.reflect()` calls `contextResolver.resolve(...)` once and passes the resulting `entries` array to `PromptBuilder.buildUserMessage()`, replacing today's single-entry call.

### Ribbon + idle-state wiring

- `main.ts` retains the `HTMLElement` returned by `addRibbonIcon(...)` and toggles a `dana-ribbon-passive` CSS class based on `ContextResolver`/`JournalDetector` output.
- The listener is registered via `this.registerEvent(this.app.workspace.on('active-leaf-change', ...))` so Obsidian tears it down automatically on unload.
- `DanaPanel`'s IDLE render reflects the same passive/active status in its copy (per the design spec's "Open a journal note to reflect" passive state), without blocking the cross-entry chips ("How have I been lately?", "What's been on my mind?") — only the active-note-flavored framing changes.

### Prompt rewrite for synthesis

`PromptBuilder.SYSTEM_PROMPT` and `buildUserMessage()` are rewritten to instruct the model to find and name a thread that recurs across at least two different days when multiple entries are available (a feeling, tension, or topic that repeats), rather than summarizing the single most recent entry. When only one entry exists (cold start, or active note isn't a journal note and the folder has just one entry), the prompt falls back to today's single-entry framing.

### API key encryption: `SecretStore`

Dana is desktop-only (mobile is already a stated non-goal), so Electron's `safeStorage` API is available. New `SecretStore` class wraps it:

```typescript
class SecretStore {
  constructor(private safeStorage: Pick<typeof import('electron').safeStorage, 'isEncryptionAvailable' | 'encryptString' | 'decryptString'>) {}

  encrypt(plaintext: string): string | null;  // returns null if unavailable
  decrypt(ciphertext: string): string | null; // returns null on failure
}
```

- `safeStorage` is injected rather than `require('electron')`'d directly inside the class, so it's unit-testable with a fake.
- Settings store an `openaiKeyEncrypted: string` (base64) field instead of plaintext `openaiKey`. On load, any existing plaintext `openaiKey` from prior versions is transparently encrypted and migrated.
- If `safeStorage.isEncryptionAvailable()` is false (some Linux configs without a keyring), the settings UI says so honestly rather than implying protection that isn't there, and falls back to plaintext storage with a one-time `Notice` warning.
- Settings UI copy is corrected from "Stored in your vault's plugin data ... syncs if you use Obsidian Sync" to accurately describe OS-backed encryption (or the plaintext fallback state).

## Data flow (updated `reflect()`)

```
reflect(userPrompt?)
  → resolve context: ContextResolver.resolve(activeFile, frontmatter, settings)
  → entries.length === 0?
        no active file & folder empty → ERROR_NO_NOTES ("No journal notes found in [folder]. Is this the right folder?" + "Change folder →")
        active file too short & folder empty → EMPTY_NOTES ("Start writing, and Dana will reflect with you.")
  → resolve AI provider (decrypting the API key via SecretStore if OpenAI)
        unavailable → ERROR_NO_AI
  → build system/user prompt from `entries` (PromptBuilder)
  → stream response (unchanged)
```

## Error handling

- `ERROR_NO_NOTES` and `EMPTY_NOTES` are un-conflated: the former now means "the configured journal folder has no journal entries at all" (with a "Change folder →" action opening settings), matching the design spec; the latter remains "there is content but it's too short to reflect on."
- Context resolution is checked *before* AI provider availability, since there's no point prompting the user to set up AI if there's nothing to reflect on yet.
- `SecretStore` decrypt failures (e.g. vault synced to a machine where the OS keychain entry doesn't exist) clear the stored key and drop into `ERROR_NO_AI` with a re-entry nudge, instead of throwing into the reflect flow.
- The new `active-leaf-change` listener is registered via `registerEvent` to avoid leaking on plugin unload.

## Testing

- `tests/ContextResolver.test.ts` (new): active file already present in recent-entries scan (dedupe by path); active file is a journal note outside the configured folder (included anyway); active file is not a journal note (excluded); no active file; zero entries anywhere.
- `tests/PromptBuilder.test.ts` (extend): system prompt instructs cross-entry synthesis; `buildUserMessage` frames single-entry vs. multi-entry input differently.
- `tests/SecretStore.test.ts` (new): encrypt/decrypt roundtrip with a fake `safeStorage`; plaintext-migration path; unavailable-encryption fallback.
- `DanaPanel` remains without direct unit tests (Obsidian `ItemView`, not practical to isolate) — covered by a manual QA checklist instead: multi-entry folder, single-entry folder, non-journal active note, empty folder, Ollama down.

## Follow-up (not part of this implementation)

- Correct the PRD's "Local-First AI (Transformers.js)" section to reflect that only Ollama/OpenAI are currently implemented, moving Transformers.js to a clearly-marked fast-follow.
