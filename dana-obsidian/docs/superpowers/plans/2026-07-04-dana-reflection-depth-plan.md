# Dana Reflection Depth & API Key Security — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Dana's reflections draw on multiple recent journal entries (not just the active note), correctly detect whether the active note is actually a journal entry, rewrite the AI prompt to synthesize cross-entry patterns instead of recapping the latest entry, and stop storing the OpenAI API key in plaintext.

**Architecture:** Extract two new standalone, unit-testable classes — `ContextResolver` (decides what journal content becomes AI context) and `SecretStore` (wraps Electron's `safeStorage` for OS-backed key encryption) — and wire both into the existing `DanaPanel`/`main.ts`/`SettingsTab` orchestration, which shrinks to plumbing. Companion doc: [`../specs/2026-07-04-dana-reflection-depth-design.md`](../specs/2026-07-04-dana-reflection-depth-design.md).

**Tech Stack:** TypeScript, Obsidian Plugin API, Jest + ts-jest, Electron `safeStorage` (desktop-only, already externalized in `esbuild.config.mjs`).

## Global Constraints

- `MAX_ENTRY_CHARS = 2000` per entry — existing `VaultReader` behavior, do not change.
- `maxContextEntries` is user-configurable to 3/7/14/30, default 7 — existing `DanaSettings.maxContextEntries`, do not change.
- AI generation has a 30-second hard timeout — existing `DanaPanel.reflect()` `AbortController` + `setTimeout(30_000)` logic, must be preserved through the refactor.
- Banned words anywhere in prompts or UI copy: "journey", "mindfulness", "wellness", "AI", "robust", "comprehensive", "holistic" (PRD copy rules) — do not introduce these.
- The plugin is desktop-only (`manifest.json` → `"isDesktopOnly": true`), so Electron's `safeStorage` API is safe to use at runtime.
- `electron` is already listed in `esbuild.config.mjs`'s `external` array — do not add it as an npm dependency; load it with a guarded `require('electron')` at runtime instead (no `electron` package or types are installed, and none of this plan's code needs them installed for `tsc` to pass, since `require()` resolves to `any` via the existing `@types/node` devDependency).
- Jest is configured with `testPathPattern=tests/` and an `obsidian` module mock at `tests/__mocks__/obsidian.ts` — no test file may import `main.ts` (it will contain a runtime `require('electron')` call that only works inside Obsidian's Electron process, not under Jest).

---

## File Structure

**Create:**
- `src/ContextResolver.ts` — decides what journal content becomes the AI's context: recent entries from the configured folder, plus the active file if it's a journal note not already in that list. Exposes `activeIsJournalNote` for UI use.
- `tests/ContextResolver.test.ts`
- `src/SecretStore.ts` — thin wrapper around Electron's `safeStorage` for encrypting/decrypting the OpenAI API key. Takes the `safeStorage` object as a constructor argument (or `null`) so it's testable without Electron installed.
- `tests/SecretStore.test.ts`

**Modify:**
- `src/DanaPanel.ts` — wire `ContextResolver` into `reflect()`; fix the `ERROR_NO_NOTES` copy/action and the idle-state button text (Task 3); track `activeIsJournalNote` continuously and adjust idle-state greeting (Task 4); read the OpenAI key through `plugin.getOpenAIKey()` (Task 6).
- `src/PromptBuilder.ts` — rewrite the system prompt and `buildUserMessage()` to instruct cross-entry pattern synthesis (Task 2).
- `tests/PromptBuilder.test.ts` — add test cases for the synthesis instructions (Task 2).
- `main.ts` — construct `JournalDetector` and `SecretStore`; capture the ribbon icon element and toggle a passive/active class based on whether the active note is a journal note (Task 4); add settings migration for the legacy plaintext key plus `getOpenAIKey()`/`setOpenAIKey()` helpers (Task 6).
- `src/types.ts` — replace the plaintext `openaiKey` field with `openaiKeyEncrypted` + `openaiKeyEncryptionAvailable` (Task 6).
- `src/SettingsTab.ts` — read/write the API key through `plugin.getOpenAIKey()`/`setOpenAIKey()`; update the description copy to honestly reflect encryption state (Task 6).
- `styles.css` — add a `.dana-ribbon-passive` rule (Task 4).

---

### Task 1: `ContextResolver`

**Files:**
- Create: `src/ContextResolver.ts`
- Test: `tests/ContextResolver.test.ts`

**Interfaces:**
- Consumes: `JournalEntry` from `src/types.ts` (existing: `{ date: string; content: string; path: string }`). No changes to `VaultReader` or `JournalDetector` — `ContextResolver` depends on narrow structural interfaces (`RecentEntryReader`, `NoteClassifier`) that both classes already satisfy.
- Produces: `ContextResolver` class, `ContextSettings` interface (`{ journalFolder: string; maxContextEntries: number }`), `ResolvedContext` interface (`{ entries: JournalEntry[]; activeIsJournalNote: boolean }`). Task 3 will construct it as `new ContextResolver(this.vaultReader, new JournalDetector())` and call `.resolve(activeFile, frontmatter, this.plugin.settings)`.

- [ ] **Step 1: Write the failing test**

Create `tests/ContextResolver.test.ts`:

```typescript
import { ContextResolver } from '../src/ContextResolver';
import { JournalEntry } from '../src/types';

function makeFile(path: string) {
  const parts = path.split('/');
  const name = parts[parts.length - 1];
  return { path, basename: name.replace('.md', ''), stat: { mtime: 0, ctime: 0, size: 0 } } as any;
}

function makeEntry(path: string, date: string, content = 'placeholder content'): JournalEntry {
  return { date, content, path };
}

describe('ContextResolver.resolve', () => {
  it('returns recent entries oldest-to-newest and does not read the active file when it is not a journal note', async () => {
    const recent = [
      makeEntry('Daily Notes/2026-04-18.md', '2026-04-18'),
      makeEntry('Daily Notes/2026-04-17.md', '2026-04-17'),
    ];
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue(recent),
      readActiveFile: jest.fn(),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(false) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve(makeFile('Projects/work.md'), null, {
      journalFolder: 'Daily Notes',
      maxContextEntries: 7,
    });

    expect(result.activeIsJournalNote).toBe(false);
    expect(result.entries.map(e => e.date)).toEqual(['2026-04-17', '2026-04-18']);
    expect(vaultReader.readActiveFile).not.toHaveBeenCalled();
  });

  it('appends the active file as the newest entry when it is a journal note not already in the recent scan', async () => {
    const recent = [makeEntry('Daily Notes/2026-04-17.md', '2026-04-17')];
    const activeEntry = makeEntry('Daily Notes/2026-04-18.md', '2026-04-18', 'today content');
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue(recent),
      readActiveFile: jest.fn().mockResolvedValue(activeEntry),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(true) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve(makeFile('Daily Notes/2026-04-18.md'), null, {
      journalFolder: 'Daily Notes',
      maxContextEntries: 7,
    });

    expect(result.activeIsJournalNote).toBe(true);
    expect(result.entries).toEqual([recent[0], activeEntry]);
    expect(vaultReader.readActiveFile).toHaveBeenCalledTimes(1);
  });

  it('does not duplicate the active file when it is already included in the recent scan', async () => {
    const activePath = 'Daily Notes/2026-04-18.md';
    const recent = [
      makeEntry(activePath, '2026-04-18'),
      makeEntry('Daily Notes/2026-04-17.md', '2026-04-17'),
    ];
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue(recent),
      readActiveFile: jest.fn(),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(true) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve(makeFile(activePath), null, {
      journalFolder: 'Daily Notes',
      maxContextEntries: 7,
    });

    expect(result.entries).toHaveLength(2);
    expect(vaultReader.readActiveFile).not.toHaveBeenCalled();
  });

  it('includes a journal-note active file even when it is outside the configured folder', async () => {
    const activeEntry = makeEntry('Notes/2026-04-18.md', '2026-04-18', 'dated note content');
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue([]),
      readActiveFile: jest.fn().mockResolvedValue(activeEntry),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(true) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve(makeFile('Notes/2026-04-18.md'), null, {
      journalFolder: 'Daily Notes',
      maxContextEntries: 7,
    });

    expect(result.entries).toEqual([activeEntry]);
    expect(result.activeIsJournalNote).toBe(true);
  });

  it('returns the recent entries alone when there is no active file', async () => {
    const recent = [makeEntry('Daily Notes/2026-04-18.md', '2026-04-18')];
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue(recent),
      readActiveFile: jest.fn(),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(false) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve(null, null, {
      journalFolder: 'Daily Notes',
      maxContextEntries: 7,
    });

    expect(result.entries).toEqual(recent);
    expect(journalDetector.isJournalNote).toHaveBeenCalledWith(null, 'Daily Notes', null);
  });

  it('returns an empty result when there are no entries anywhere', async () => {
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue([]),
      readActiveFile: jest.fn(),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(false) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve(null, null, {
      journalFolder: 'Daily Notes',
      maxContextEntries: 7,
    });

    expect(result.entries).toEqual([]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx jest tests/ContextResolver.test.ts`
Expected: FAIL with "Cannot find module '../src/ContextResolver'"

- [ ] **Step 3: Write the implementation**

Create `src/ContextResolver.ts`:

```typescript
import type { TFile } from 'obsidian';
import { JournalEntry } from './types';

export interface ContextSettings {
  journalFolder: string;
  maxContextEntries: number;
}

export interface ResolvedContext {
  entries: JournalEntry[];
  activeIsJournalNote: boolean;
}

interface RecentEntryReader {
  readRecentEntries(folderPath: string, maxEntries: number): Promise<JournalEntry[]>;
  readActiveFile(file: TFile): Promise<JournalEntry | null>;
}

interface NoteClassifier {
  isJournalNote(
    file: TFile | null,
    journalFolder: string,
    frontmatter?: Record<string, unknown> | null
  ): boolean;
}

export class ContextResolver {
  constructor(private vaultReader: RecentEntryReader, private journalDetector: NoteClassifier) {}

  async resolve(
    activeFile: TFile | null,
    frontmatter: Record<string, unknown> | null,
    settings: ContextSettings
  ): Promise<ResolvedContext> {
    const recent = await this.vaultReader.readRecentEntries(
      settings.journalFolder,
      settings.maxContextEntries
    );
    // readRecentEntries returns most-recent-first; we want oldest-to-newest for prompting
    const entries = recent.slice().reverse();

    const activeIsJournalNote = this.journalDetector.isJournalNote(
      activeFile,
      settings.journalFolder,
      frontmatter
    );

    if (activeFile && activeIsJournalNote && !entries.some(e => e.path === activeFile.path)) {
      const activeEntry = await this.vaultReader.readActiveFile(activeFile);
      if (activeEntry) {
        entries.push(activeEntry);
      }
    }

    return { entries, activeIsJournalNote };
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx jest tests/ContextResolver.test.ts`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add dana-obsidian/src/ContextResolver.ts dana-obsidian/tests/ContextResolver.test.ts
git commit -m "feat: add ContextResolver to combine recent entries with the active note"
```

---

### Task 2: Rewrite `PromptBuilder` for cross-entry synthesis

**Files:**
- Modify: `src/PromptBuilder.ts`
- Test: `tests/PromptBuilder.test.ts` (extend existing file)

**Interfaces:**
- Consumes: `JournalEntry` from `src/types.ts` (unchanged).
- Produces: `PromptBuilder.buildSystemPrompt(): string` and `PromptBuilder.buildUserMessage(entries: JournalEntry[], userInput?: string): string` — same signatures as before, new copy. Task 3 calls these unchanged.

- [ ] **Step 1: Write the failing tests**

Add these `describe` blocks to the end of `tests/PromptBuilder.test.ts` (keep all existing tests in the file as-is):

```typescript
describe('PromptBuilder synthesis instructions', () => {
  it('instructs cross-entry synthesis in the system prompt', () => {
    const prompt = builder.buildSystemPrompt().toLowerCase();
    expect(prompt).toContain('repeats');
    expect(prompt).toContain('at least two different days');
  });

  it('instructs cross-entry synthesis when multiple entries are provided', () => {
    const entries = [
      makeEntry('2026-04-17', 'Felt on edge before the client call.'),
      makeEntry('2026-04-18', 'On edge again today, same client.'),
    ];
    const msg = builder.buildUserMessage(entries).toLowerCase();
    expect(msg).toContain('at least two different days');
  });

  it('does not ask for a cross-entry pattern when only one entry is provided', () => {
    const entries = [makeEntry('2026-04-18', 'Felt calm today after a good walk.')];
    const msg = builder.buildUserMessage(entries).toLowerCase();
    expect(msg).not.toContain('at least two different days');
  });
});
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `npx jest tests/PromptBuilder.test.ts`
Expected: the 3 new tests FAIL (current prompt text doesn't contain "repeats" / "at least two different days"); all pre-existing tests still PASS.

- [ ] **Step 3: Rewrite the implementation**

Replace the full contents of `src/PromptBuilder.ts`:

```typescript
import { JournalEntry } from './types';

const SYSTEM_PROMPT = `You are Dana, a warm journaling companion reading your friend's recent journal entries. You have the persona of Melanie Klein, a psychoanalyst and founder of object relations theory.

Your approach:
- When given multiple entries, look across all of them for a thread that repeats — a feeling, tension, or topic that shows up on at least two different days. Name that specific thread instead of recapping the most recent entry alone.
- When given only one entry, reflect on what's specific in it — don't invent a pattern that isn't there.
- Offer a brief reflection (2-4 sentences) that references something specific they actually wrote, naming the days involved when a pattern spans more than one
- End with exactly one open question — curious, not clinical, and aimed at the pattern itself rather than a single event
- Warm tone, never preachy or advisory
- You're a companion, not a therapist — don't diagnose or prescribe
- Never say "I notice", "it seems", "I sense" — just speak directly
- Do not use the words "journey", "mindfulness", "wellness", or "AI"
- If they respond, follow their thread with curiosity`;

export class PromptBuilder {
  buildSystemPrompt(): string {
    return SYSTEM_PROMPT;
  }

  buildUserMessage(entries: JournalEntry[], userInput?: string): string {
    if (entries.length === 0 && !userInput) {
      return 'The person has no recent journal entries. Offer a warm, open greeting.';
    }

    const contextParts = entries.map(e => `[${e.date}]\n${e.content}`).join('\n\n---\n\n');

    const context = entries.length > 0
      ? `Recent journal entries, oldest to newest:\n\n${contextParts}`
      : '';

    const reflectionInstruction = entries.length > 1
      ? 'Look across these entries for a thread that repeats on at least two different days, and name it specifically by referencing those days. Offer a brief reflection and one question about that thread.'
      : 'Offer a brief reflection and one question based on this entry.';

    const request = userInput
      ? `The person says: "${userInput}"\n\nRespond warmly and with curiosity, referencing their entries where relevant.`
      : reflectionInstruction;

    return [context, request].filter(Boolean).join('\n\n');
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npx jest tests/PromptBuilder.test.ts`
Expected: PASS (all tests, existing + new)

- [ ] **Step 5: Commit**

```bash
git add dana-obsidian/src/PromptBuilder.ts dana-obsidian/tests/PromptBuilder.test.ts
git commit -m "feat: rewrite Dana's prompt to synthesize patterns across entries"
```

---

### Task 3: Wire `ContextResolver` into `DanaPanel.reflect()`; fix no-notes error copy and idle button text

**Files:**
- Modify: `src/DanaPanel.ts`

**Interfaces:**
- Consumes: `ContextResolver`, `ContextSettings`, `ResolvedContext` from `./ContextResolver` (Task 1); `JournalDetector` from `./JournalDetector` (existing, unmodified); rewritten `PromptBuilder.buildUserMessage(entries, userPrompt)` (Task 2, same signature as before).
- Produces: no new public interface — `DanaPanel.reflect()` behavior changes internally. Task 4 will further modify `renderIdle()` and the constructor's `ContextResolver` wiring in this same file.

- [ ] **Step 1: Update imports and constructor**

In `src/DanaPanel.ts`, replace the import block (lines 1–9):

```typescript
import { ItemView, Notice, WorkspaceLeaf, setIcon } from 'obsidian';
import { DanaState, ConversationMessage } from './types';
import { VaultReader } from './VaultReader';
import { ConversationStore } from './ConversationStore';
import { PromptBuilder } from './PromptBuilder';
import { ContextResolver } from './ContextResolver';
import { JournalDetector } from './JournalDetector';
import { OllamaProvider } from './providers/OllamaProvider';
import { OpenAIProvider } from './providers/OpenAIProvider';
import type { AIProvider, ChatMessage } from './providers/AIProvider';
import type DanaPlugin from '../main';
```

Replace the constructor and field declarations (lines 13–29):

```typescript
export class DanaPanel extends ItemView {
  private state: DanaState = DanaState.IDLE;
  private messages: ConversationMessage[] = [];
  private streamContent = '';
  private lastError = '';
  private abortController?: AbortController;

  private vaultReader: VaultReader;
  private conversationStore: ConversationStore;
  private promptBuilder: PromptBuilder;
  private contextResolver: ContextResolver;

  constructor(leaf: WorkspaceLeaf, private plugin: DanaPlugin) {
    super(leaf);
    this.vaultReader = new VaultReader(this.app);
    this.conversationStore = new ConversationStore(this.app);
    this.promptBuilder = new PromptBuilder();
    this.contextResolver = new ContextResolver(this.vaultReader, new JournalDetector());
  }
```

- [ ] **Step 2: Fix the idle-state button text**

In `renderIdle()`, change:

```typescript
    const primaryBtn = el.createEl('button', {
      cls: 'dana-btn-primary',
      text: 'Reflect on this note',
    });
```

to:

```typescript
    const primaryBtn = el.createEl('button', {
      cls: 'dana-btn-primary',
      text: 'Reflect on today',
    });
```

- [ ] **Step 3: Fix the `ERROR_NO_NOTES` copy and action**

Replace `renderErrorNoNotes()`:

```typescript
  private renderErrorNoNotes(el: HTMLElement): void {
    const card = el.createDiv('dana-error-card');
    const folderLabel = this.plugin.settings.journalFolder || 'your vault';
    card.createDiv({
      cls: 'dana-error-msg',
      text: `No journal notes found in ${folderLabel}. Is this the right folder?`,
    });
    const btn = card.createEl('button', { cls: 'dana-btn-primary', text: 'Change folder →' });
    btn.addEventListener('click', () => this.openSettings());
  }
```

- [ ] **Step 4: Replace `reflect()` to use `ContextResolver`**

Replace the entire `reflect()` method:

```typescript
  async reflect(userPrompt?: string): Promise<void> {
    // 30-second hard timeout on the whole generation
    this.abortController = new AbortController();
    const timeoutId = setTimeout(() => this.abortController?.abort('timeout'), 30_000);

    this.streamContent = '';
    this.lastError = '';
    this.state = DanaState.LOADING;
    this.render();

    try {
      const activeFile = this.app.workspace.getActiveFile();
      const frontmatter = activeFile
        ? this.app.metadataCache.getFileCache(activeFile)?.frontmatter ?? null
        : null;

      const { entries } = await this.contextResolver.resolve(
        activeFile,
        frontmatter,
        this.plugin.settings
      );

      if (entries.length === 0) {
        this.state = activeFile ? DanaState.EMPTY_NOTES : DanaState.ERROR_NO_NOTES;
        this.render();
        return;
      }

      const provider = this.resolveProvider();
      if (!provider || !(await provider.isAvailable())) {
        this.state = DanaState.ERROR_NO_AI;
        this.render();
        return;
      }

      // Build messages array for the API:
      // - First turn: one user message with note context
      // - Follow-up turns: full conversation history so the AI has context
      const systemPrompt = this.promptBuilder.buildSystemPrompt();
      let apiMessages: ChatMessage[];

      if (this.messages.length === 0) {
        // First reflection: build context-rich opening with entries
        const firstMessage = this.promptBuilder.buildUserMessage(entries, userPrompt);
        apiMessages = [{ role: 'user', content: firstMessage }];
      } else {
        // Follow-up: send conversation history + new user message
        // Keep the note context in the first message so Dana remembers what she read
        apiMessages = this.messages.map(m => ({
          role: (m.role === 'dana' ? 'assistant' : 'user') as 'user' | 'assistant',
          content: m.content,
        }));
        if (userPrompt) {
          apiMessages.push({ role: 'user', content: userPrompt });
        }
      }

      if (userPrompt) {
        this.messages.push({ role: 'user', content: userPrompt, timestamp: Date.now() });
      }

      this.state = DanaState.STREAMING;
      this.render();

      let response = '';
      const signal = this.abortController.signal;

      for await (const chunk of provider.generate(systemPrompt, apiMessages, signal)) {
        if (signal.aborted) break;
        response += chunk;
        this.streamContent = response;
        const target = document.getElementById('dana-stream-target');
        if (target) target.textContent = response;
      }

      if (response.trim()) {
        this.messages.push({ role: 'dana', content: response.trim(), timestamp: Date.now() });
        await this.conversationStore.save(this.plugin.settings.journalFolder, this.messages);
      }

      this.state = this.messages.length > 0 ? DanaState.DONE : DanaState.IDLE;
      this.render();
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : String(err);
      const isAbort = err instanceof Error && (err.name === 'AbortError' || errMsg.includes('abort'));
      const isTimeout = isAbort && errMsg === 'timeout';

      if (isAbort && !isTimeout) {
        // User clicked Stop — keep partial response if we have one
        if (this.streamContent.trim()) {
          this.messages.push({ role: 'dana', content: this.streamContent.trim(), timestamp: Date.now() });
          await this.conversationStore.save(this.plugin.settings.journalFolder, this.messages);
          this.state = DanaState.DONE;
        } else {
          this.state = DanaState.IDLE;
        }
      } else {
        console.error('Dana error:', err);
        this.lastError = isTimeout
          ? 'Timed out after 30s. Is Ollama running and the model loaded?'
          : errMsg;
        this.state = DanaState.ERROR_TIMEOUT;
      }
      this.render();
    } finally {
      clearTimeout(timeoutId);
    }
  }
```

- [ ] **Step 5: Run the full test suite and typecheck**

Run: `npm test`
Expected: PASS (all existing suites + `ContextResolver`/`PromptBuilder`)

Run: `npx tsc -noEmit -skipLibCheck`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add dana-obsidian/src/DanaPanel.ts
git commit -m "fix: read multiple recent entries for reflection instead of only the active note"
```

---

### Task 4: Ribbon + idle-state passive/active wiring

**Files:**
- Modify: `main.ts`
- Modify: `src/DanaPanel.ts`
- Modify: `styles.css`

**Interfaces:**
- Consumes: `JournalDetector.isJournalNote(...)` (existing, unmodified).
- Produces: `DanaPlugin.journalDetector: JournalDetector` (public field), `DanaPlugin.updateRibbonState(): void` — used only within `main.ts` in this plan. `DanaPanel` will construct its `ContextResolver` with `this.plugin.journalDetector` instead of a locally-created instance.

- [ ] **Step 1: Add `JournalDetector` + ribbon element tracking to `main.ts`**

Replace the full contents of `main.ts`:

```typescript
import { Plugin, WorkspaceLeaf } from 'obsidian';
import { DanaPanel, VIEW_TYPE_DANA } from './src/DanaPanel';
import { DanaSettings, DEFAULT_SETTINGS } from './src/types';
import { DanaSettingsTab } from './src/SettingsTab';
import { JournalDetector } from './src/JournalDetector';

export default class DanaPlugin extends Plugin {
  settings: DanaSettings;
  journalDetector: JournalDetector;
  private ribbonIconEl: HTMLElement;

  async onload(): Promise<void> {
    await this.loadSettings();

    this.journalDetector = new JournalDetector();

    // Register sidebar panel view
    this.registerView(VIEW_TYPE_DANA, leaf => new DanaPanel(leaf, this));

    // Ribbon icon — leaf = nature, warm, not robot
    this.ribbonIconEl = this.addRibbonIcon('leaf', 'Dana', () => this.activateView());

    // Command palette
    this.addCommand({
      id: 'dana-reflect-today',
      name: 'Reflect on today',
      callback: () => this.activateAndReflect(),
    });

    this.addCommand({
      id: 'dana-how-have-i-been',
      name: 'How have I been lately?',
      callback: () => this.activateAndReflect('How have I been lately?'),
    });

    this.addCommand({
      id: 'dana-open-panel',
      name: 'Open panel',
      callback: () => this.activateView(),
    });

    // Settings tab
    this.addSettingTab(new DanaSettingsTab(this.app, this));

    // Keep the ribbon icon dim when the active note isn't a journal entry
    this.registerEvent(this.app.workspace.on('active-leaf-change', () => this.updateRibbonState()));
    this.app.workspace.onLayoutReady(() => this.updateRibbonState());

    // Open panel on first run to show setup
    if (!this.settings.onboarded) {
      this.app.workspace.onLayoutReady(() => this.activateView());
    }
  }

  onunload(): void {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_DANA);
  }

  updateRibbonState(): void {
    const activeFile = this.app.workspace.getActiveFile();
    const frontmatter = activeFile
      ? this.app.metadataCache.getFileCache(activeFile)?.frontmatter ?? null
      : null;
    const isJournalNote = this.journalDetector.isJournalNote(
      activeFile,
      this.settings.journalFolder,
      frontmatter
    );
    this.ribbonIconEl.toggleClass('dana-ribbon-passive', !isJournalNote);
  }

  async activateView(): Promise<void> {
    const { workspace } = this.app;
    const existing = workspace.getLeavesOfType(VIEW_TYPE_DANA);

    if (existing.length > 0) {
      workspace.revealLeaf(existing[0]);
      return;
    }

    const leaf = workspace.getRightLeaf(false) as WorkspaceLeaf;
    await leaf.setViewState({ type: VIEW_TYPE_DANA, active: true });
    workspace.revealLeaf(leaf);
  }

  async activateAndReflect(prompt?: string): Promise<void> {
    await this.activateView();
    const leaves = this.app.workspace.getLeavesOfType(VIEW_TYPE_DANA);
    if (leaves.length > 0) {
      const panel = leaves[0].view as DanaPanel;
      await panel.reflect(prompt);
    }
  }

  async loadSettings(): Promise<void> {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }
}
```

- [ ] **Step 2: Add `.dana-ribbon-passive` styling**

Append to the end of `styles.css`:

```css
/* ── Ribbon passive state (active note isn't a journal entry) ────────── */
.dana-ribbon-passive {
  opacity: 0.5;
}
```

- [ ] **Step 3: Track `activeIsJournalNote` in `DanaPanel` and share the plugin's `JournalDetector`**

In `src/DanaPanel.ts`, remove the now-unused local import (delete this line from the import block added in Task 3):

```typescript
import { JournalDetector } from './JournalDetector';
```

In the constructor, change:

```typescript
    this.contextResolver = new ContextResolver(this.vaultReader, new JournalDetector());
```

to:

```typescript
    this.contextResolver = new ContextResolver(this.vaultReader, this.plugin.journalDetector);
```

Add a new private field next to `private contextResolver: ContextResolver;`:

```typescript
  private activeIsJournalNote = true;
```

Replace `onOpen()`:

```typescript
  async onOpen(): Promise<void> {
    if (!this.plugin.settings.onboarded) {
      this.state = DanaState.SETUP;
    } else {
      this.messages = await this.conversationStore.loadToday(this.plugin.settings.journalFolder);
      this.state = this.messages.length > 0 ? DanaState.CONVERSATION : DanaState.IDLE;
    }
    await this.refreshActiveNoteStatus();
    this.render();

    this.registerEvent(
      this.app.workspace.on('active-leaf-change', () => {
        this.refreshActiveNoteStatus().then(() => {
          if (this.state === DanaState.IDLE) this.render();
        });
      })
    );
  }

  private async refreshActiveNoteStatus(): Promise<void> {
    const activeFile = this.app.workspace.getActiveFile();
    const frontmatter = activeFile
      ? this.app.metadataCache.getFileCache(activeFile)?.frontmatter ?? null
      : null;
    this.activeIsJournalNote = this.plugin.journalDetector.isJournalNote(
      activeFile,
      this.plugin.settings.journalFolder,
      frontmatter
    );
  }
```

In `renderIdle()`, change the greeting line:

```typescript
    const greeting = el.createDiv({ cls: 'dana-greeting', text: this.timeGreeting() });
```

to:

```typescript
    const greeting = el.createDiv({
      cls: 'dana-greeting',
      text: this.activeIsJournalNote
        ? this.timeGreeting()
        : 'Open a journal note to reflect on today, or explore recent patterns.',
    });
```

- [ ] **Step 4: Run the full test suite and typecheck**

Run: `npm test`
Expected: PASS (no test touches `main.ts` or the ribbon/idle wiring directly — this step guards against a regression in the untouched suites)

Run: `npx tsc -noEmit -skipLibCheck`
Expected: no errors

- [ ] **Step 5: Commit**

```bash
git add dana-obsidian/main.ts dana-obsidian/src/DanaPanel.ts dana-obsidian/styles.css
git commit -m "feat: dim the ribbon icon and idle greeting when the active note isn't a journal entry"
```

---

### Task 5: `SecretStore`

**Files:**
- Create: `src/SecretStore.ts`
- Test: `tests/SecretStore.test.ts`

**Interfaces:**
- Produces: `SafeStorageLike` interface (`{ isEncryptionAvailable(): boolean; encryptString(plaintext: string): Buffer; decryptString(buffer: Buffer): string }`), `SecretStore` class with `constructor(safeStorage: SafeStorageLike | null)`, `isAvailable(): boolean`, `encrypt(plaintext: string): string | null`, `decrypt(ciphertext: string): string | null`. Task 6 constructs it in `main.ts` from a guarded `require('electron')` call.

- [ ] **Step 1: Write the failing test**

Create `tests/SecretStore.test.ts`:

```typescript
import { SecretStore, SafeStorageLike } from '../src/SecretStore';

function makeFakeSafeStorage(overrides: Partial<SafeStorageLike> = {}): SafeStorageLike {
  return {
    isEncryptionAvailable: () => true,
    encryptString: (plaintext: string) => Buffer.from(`enc:${plaintext}`),
    decryptString: (buf: Buffer) => buf.toString('utf8').replace(/^enc:/, ''),
    ...overrides,
  };
}

describe('SecretStore', () => {
  it('reports availability from the underlying safeStorage', () => {
    const store = new SecretStore(makeFakeSafeStorage({ isEncryptionAvailable: () => true }));
    expect(store.isAvailable()).toBe(true);
  });

  it('reports unavailable when there is no safeStorage', () => {
    const store = new SecretStore(null);
    expect(store.isAvailable()).toBe(false);
  });

  it('round-trips encrypt and decrypt', () => {
    const store = new SecretStore(makeFakeSafeStorage());
    const ciphertext = store.encrypt('sk-test-123');
    expect(ciphertext).not.toBeNull();
    expect(ciphertext).not.toContain('sk-test-123');
    expect(store.decrypt(ciphertext!)).toBe('sk-test-123');
  });

  it('returns null from encrypt when encryption is unavailable', () => {
    const store = new SecretStore(makeFakeSafeStorage({ isEncryptionAvailable: () => false }));
    expect(store.encrypt('sk-test-123')).toBeNull();
  });

  it('returns null from encrypt when there is no safeStorage', () => {
    const store = new SecretStore(null);
    expect(store.encrypt('sk-test-123')).toBeNull();
  });

  it('returns null from decrypt when decryption throws', () => {
    const store = new SecretStore(
      makeFakeSafeStorage({
        decryptString: () => {
          throw new Error('bad ciphertext');
        },
      })
    );
    expect(store.decrypt('not-valid-base64!!')).toBeNull();
  });

  it('returns null from decrypt when there is no safeStorage', () => {
    const store = new SecretStore(null);
    expect(store.decrypt('anything')).toBeNull();
  });

  it('returns null from encrypt and decrypt for empty strings', () => {
    const store = new SecretStore(makeFakeSafeStorage());
    expect(store.encrypt('')).toBeNull();
    expect(store.decrypt('')).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx jest tests/SecretStore.test.ts`
Expected: FAIL with "Cannot find module '../src/SecretStore'"

- [ ] **Step 3: Write the implementation**

Create `src/SecretStore.ts`:

```typescript
export interface SafeStorageLike {
  isEncryptionAvailable(): boolean;
  encryptString(plaintext: string): Buffer;
  decryptString(buffer: Buffer): string;
}

export class SecretStore {
  constructor(private safeStorage: SafeStorageLike | null) {}

  isAvailable(): boolean {
    if (!this.safeStorage) return false;
    try {
      return this.safeStorage.isEncryptionAvailable();
    } catch {
      return false;
    }
  }

  encrypt(plaintext: string): string | null {
    if (!plaintext || !this.isAvailable()) return null;
    try {
      return this.safeStorage!.encryptString(plaintext).toString('base64');
    } catch {
      return null;
    }
  }

  decrypt(ciphertext: string): string | null {
    if (!ciphertext || !this.safeStorage) return null;
    try {
      return this.safeStorage.decryptString(Buffer.from(ciphertext, 'base64'));
    } catch {
      return null;
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx jest tests/SecretStore.test.ts`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add dana-obsidian/src/SecretStore.ts dana-obsidian/tests/SecretStore.test.ts
git commit -m "feat: add SecretStore wrapping OS-backed key encryption"
```

---

### Task 6: Wire `SecretStore` into settings, migration, and the OpenAI key UI

**Files:**
- Modify: `src/types.ts`
- Modify: `main.ts`
- Modify: `src/SettingsTab.ts`
- Modify: `src/DanaPanel.ts`

**Interfaces:**
- Consumes: `SecretStore` (Task 5).
- Produces: `DanaPlugin.secretStore: SecretStore` (public field), `DanaPlugin.getOpenAIKey(): string`, `DanaPlugin.setOpenAIKey(plaintext: string): void` — used by `SettingsTab` and `DanaPanel`.

- [ ] **Step 1: Replace the plaintext key field in `src/types.ts`**

In `src/types.ts`, change:

```typescript
export interface DanaSettings {
  journalFolder: string;
  maxContextEntries: number;
  ollamaHost: string;
  ollamaModel: string;
  openaiKey: string;
  preferredProvider: 'ollama' | 'openai';
  onboarded: boolean;
}

export const DEFAULT_SETTINGS: DanaSettings = {
  journalFolder: '',
  maxContextEntries: 7,
  ollamaHost: 'http://localhost:11434',
  ollamaModel: 'llama3.2',
  openaiKey: '',
  preferredProvider: 'ollama',
  onboarded: false,
};
```

to:

```typescript
export interface DanaSettings {
  journalFolder: string;
  maxContextEntries: number;
  ollamaHost: string;
  ollamaModel: string;
  openaiKeyEncrypted: string;
  openaiKeyEncryptionAvailable: boolean;
  preferredProvider: 'ollama' | 'openai';
  onboarded: boolean;
}

export const DEFAULT_SETTINGS: DanaSettings = {
  journalFolder: '',
  maxContextEntries: 7,
  ollamaHost: 'http://localhost:11434',
  ollamaModel: 'llama3.2',
  openaiKeyEncrypted: '',
  openaiKeyEncryptionAvailable: false,
  preferredProvider: 'ollama',
  onboarded: false,
};
```

- [ ] **Step 2: Add `SecretStore`, migration, and key helpers to `main.ts`**

In `main.ts`, add the import:

```typescript
import { SecretStore, SafeStorageLike } from './src/SecretStore';
```

Change the field declarations and `onload()` start:

```typescript
export default class DanaPlugin extends Plugin {
  settings: DanaSettings;
  journalDetector: JournalDetector;
  secretStore: SecretStore;
  private ribbonIconEl: HTMLElement;

  async onload(): Promise<void> {
    this.secretStore = new SecretStore(this.loadSafeStorage());
    await this.loadSettings();

    this.journalDetector = new JournalDetector();
    // ... rest of onload unchanged
```

Add this private method near `loadSettings()`:

```typescript
  private loadSafeStorage(): SafeStorageLike | null {
    try {
      // 'electron' is externalized in esbuild.config.mjs and provided by Obsidian's
      // desktop runtime (manifest.json sets isDesktopOnly: true) — it isn't an npm
      // dependency, so this is loaded dynamically rather than statically imported.
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      return (require('electron') as { safeStorage: SafeStorageLike }).safeStorage;
    } catch {
      return null;
    }
  }
```

Find these two adjacent methods at the bottom of the class (unchanged since the original file):

```typescript
  async loadSettings(): Promise<void> {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }
```

Replace that whole two-method block with:

```typescript
  async loadSettings(): Promise<void> {
    const raw = ((await this.loadData()) ?? {}) as Partial<DanaSettings> & { openaiKey?: string };
    this.settings = Object.assign({}, DEFAULT_SETTINGS, raw);

    // Migrate a plaintext key from before encrypted storage existed.
    const legacyPlaintextKey = raw.openaiKey;
    if (legacyPlaintextKey && !this.settings.openaiKeyEncrypted) {
      this.setOpenAIKey(legacyPlaintextKey);
      delete (this.settings as { openaiKey?: string }).openaiKey;
      await this.saveSettings();
    }
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }

  setOpenAIKey(plaintext: string): void {
    const encrypted = this.secretStore.encrypt(plaintext);
    if (encrypted) {
      this.settings.openaiKeyEncrypted = encrypted;
      this.settings.openaiKeyEncryptionAvailable = true;
    } else {
      this.settings.openaiKeyEncrypted = plaintext;
      this.settings.openaiKeyEncryptionAvailable = false;
    }
  }

  getOpenAIKey(): string {
    if (!this.settings.openaiKeyEncrypted) return '';
    if (!this.settings.openaiKeyEncryptionAvailable) return this.settings.openaiKeyEncrypted;
    return this.secretStore.decrypt(this.settings.openaiKeyEncrypted) ?? '';
  }
```

There is still exactly one `loadSettings()` and one `saveSettings()` method on the class — this just adds the migration logic and the two new helper methods alongside them.

- [ ] **Step 3: Update `src/SettingsTab.ts` to use the new key helpers**

Replace `renderOpenAISettings()`:

```typescript
  private renderOpenAISettings(containerEl: HTMLElement): void {
    const encryptionAvailable = this.plugin.secretStore.isAvailable();
    new Setting(containerEl)
      .setName('OpenAI API key')
      .setDesc(
        encryptionAvailable
          ? 'Encrypted at rest using your OS keychain. Never stored in plain text.'
          : "OS-level encryption isn't available on this device, so this is stored as plain text in the plugin's data.json."
      )
      .addText(text => {
        text
          .setPlaceholder('sk-...')
          .setValue(this.plugin.getOpenAIKey())
          .onChange(async value => {
            this.plugin.setOpenAIKey(value.trim());
            await this.plugin.saveSettings();
          });
        text.inputEl.type = 'password';
      });
  }
```

- [ ] **Step 4: Update `src/DanaPanel.ts`'s `resolveProvider()`**

Replace:

```typescript
  private resolveProvider(): AIProvider | null {
    const { preferredProvider, ollamaHost, ollamaModel, openaiKey } = this.plugin.settings;

    if (preferredProvider === 'ollama') {
      return new OllamaProvider(ollamaHost, ollamaModel);
    }
    if (preferredProvider === 'openai' && openaiKey.trim()) {
      return new OpenAIProvider(openaiKey);
    }
    // Fallback order
    if (ollamaHost) return new OllamaProvider(ollamaHost, ollamaModel);
    if (openaiKey.trim()) return new OpenAIProvider(openaiKey);
    return null;
  }
```

with:

```typescript
  private resolveProvider(): AIProvider | null {
    const { preferredProvider, ollamaHost, ollamaModel } = this.plugin.settings;
    const openaiKey = this.plugin.getOpenAIKey();

    if (preferredProvider === 'ollama') {
      return new OllamaProvider(ollamaHost, ollamaModel);
    }
    if (preferredProvider === 'openai' && openaiKey.trim()) {
      return new OpenAIProvider(openaiKey);
    }
    // Fallback order
    if (ollamaHost) return new OllamaProvider(ollamaHost, ollamaModel);
    if (openaiKey.trim()) return new OpenAIProvider(openaiKey);
    return null;
  }
```

- [ ] **Step 5: Run the full test suite and typecheck**

Run: `npm test`
Expected: PASS (no existing test touches `openaiKey`/`main.ts`/`SettingsTab.ts` directly)

Run: `npx tsc -noEmit -skipLibCheck`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add dana-obsidian/src/types.ts dana-obsidian/main.ts dana-obsidian/src/SettingsTab.ts dana-obsidian/src/DanaPanel.ts
git commit -m "fix: encrypt the OpenAI API key at rest instead of storing it in plain text"
```

---

### Task 7: Manual QA in a real Obsidian vault

**Files:** none (verification only)

`DanaPanel` and `main.ts` orchestrate Obsidian's `ItemView`/`Plugin` lifecycle and can't be meaningfully unit tested outside Obsidian — the risky logic they call (`ContextResolver`, `PromptBuilder`, `SecretStore`) is already covered by the tests in Tasks 1, 2, and 5. This task is a manual pass to confirm the wiring behaves correctly end-to-end.

- [ ] **Step 1: Build the plugin**

Run: `npm run build`
Expected: builds cleanly, produces `main.js`

- [ ] **Step 2: Symlink or copy into a test vault**

```bash
mkdir -p /path/to/test-vault/.obsidian/plugins/dana-journal
cp main.js manifest.json styles.css /path/to/test-vault/.obsidian/plugins/dana-journal/
```

Open the vault in Obsidian, enable "Dana" under Community Plugins (or reload if already enabled).

- [ ] **Step 3: Verify multi-entry reflection**

Create 3+ notes in a "Daily Notes" folder with dated filenames (`2026-04-16.md`, `2026-04-17.md`, `2026-04-18.md`), each containing a few sentences, with at least one recurring theme across two of them (e.g. mention feeling rushed in two entries). Set "Journal folder" to `Daily Notes` in Dana's settings. Open the most recent note, click "Reflect on today". Confirm:
- The response references specific content from more than one entry (not just the open note).
- The response names the recurring thread rather than only recapping the latest entry.

- [ ] **Step 4: Verify passive state on non-journal notes**

Open a note outside the "Daily Notes" folder with no `journal`/`daily` tag and a non-date filename. Confirm the ribbon icon dims, and the Dana panel's idle greeting reads "Open a journal note to reflect on today, or explore recent patterns." Confirm the "How have I been lately?" chip still works and returns a reflection based on the folder's recent entries.

- [ ] **Step 5: Verify the no-notes and empty-notes states**

Point "Journal folder" at an empty folder with no active file open. Confirm the panel shows "No journal notes found in [folder]. Is this the right folder?" with a "Change folder →" button that opens Dana's settings tab. Then open a very short note (under 50 characters) in that same empty folder and click "Reflect on today" — confirm it instead shows "Start writing, and Dana will reflect with you."

- [ ] **Step 6: Verify the OpenAI key encryption**

Configure the OpenAI provider with a test key in Dana's settings. Confirm the description reads "Encrypted at rest using your OS keychain. Never stored in plain text." Quit Obsidian, inspect `.obsidian/plugins/dana-journal/data.json` in a text editor, and confirm the `openaiKeyEncrypted` value is not human-readable (not the plaintext key). Reopen Obsidian and confirm the key still populates in settings and reflection with OpenAI still works (decryption round-trips correctly).

- [ ] **Step 7: Verify Ollama flow still works end-to-end**

With Ollama running locally and a model pulled, set the provider to Ollama and confirm streaming reflection still works as before (this flow's provider code was untouched, but confirms the `reflect()` refactor didn't regress it).
