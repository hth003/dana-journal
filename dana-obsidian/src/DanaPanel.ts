import { ItemView, MarkdownRenderer, Notice, WorkspaceLeaf, setIcon } from 'obsidian';
import { DanaState, ConversationSession, JournalEntry, ReflectionMode } from './types';
import { VaultReader } from './VaultReader';
import { ConversationStore } from './ConversationStore';
import { PromptBuilder } from './PromptBuilder';
import { ContextResolver } from './ContextResolver';
import { OllamaProvider } from './providers/OllamaProvider';
import { OpenAIProvider } from './providers/OpenAIProvider';
import type { AIProvider } from './providers/AIProvider';
import type DanaPlugin from '../main';

export const VIEW_TYPE_DANA = 'dana-journal-view';

/**
 * Conversation lifecycle:
 *
 *   IDLE ──[button/command, mode]──▶ startReflection(mode)
 *                                       │ resolve context ONCE
 *                                       │ pin { mode, paths, snapshot }
 *                                       ▼
 *                                 generateTurn(userInput?)
 *                                       │ re-read pinned paths (current text;
 *                                       │ snapshot fallback if file vanished)
 *                                       │ system prompt = persona + entries
 *                                       ▼
 *                                 STREAMING ──▶ DONE/CONVERSATION
 *                                       ▲              │
 *                                       └── sendMessage(text) ◀── reply box
 *
 * Timeouts: 30s to first token, then 60s between tokens. Aborts are
 * classified by `abortCause` set BEFORE calling abort() — never by
 * inspecting the rejection value (fetch rejects with strings sometimes).
 */
export class DanaPanel extends ItemView {
  private state: DanaState = DanaState.IDLE;
  private sessions: ConversationSession[] = [];
  private snapshot: JournalEntry[] = [];
  private conversationDate = '';
  private streamContent = '';
  private lastError = '';
  private abortController?: AbortController;
  private abortCause: 'ttft' | 'idle' | 'user' | null = null;

  private vaultReader: VaultReader;
  private conversationStore: ConversationStore;
  private promptBuilder: PromptBuilder;
  private contextResolver: ContextResolver;
  private activeIsJournalNote = true;

  constructor(leaf: WorkspaceLeaf, private plugin: DanaPlugin) {
    super(leaf);
    this.vaultReader = new VaultReader(this.app);
    this.conversationStore = new ConversationStore(this.app);
    this.promptBuilder = new PromptBuilder();
    this.contextResolver = new ContextResolver(this.vaultReader, this.plugin.journalDetector);
  }

  getViewType(): string { return VIEW_TYPE_DANA; }
  getDisplayText(): string { return 'Dana'; }
  getIcon(): string { return 'leaf'; }

  private get activeSession(): ConversationSession | null {
    return this.sessions.length > 0 ? this.sessions[this.sessions.length - 1] : null;
  }

  async onOpen(): Promise<void> {
    if (!this.plugin.settings.onboarded) {
      this.state = DanaState.SETUP;
    } else {
      this.conversationDate = this.conversationStore.localToday();
      this.sessions = await this.conversationStore.load(
        this.plugin.settings.journalFolder,
        this.conversationDate
      );
      const active = this.activeSession;
      if (active) {
        // Rebuild the snapshot fallback from whatever the pinned files say now.
        this.snapshot = await this.readPinned(active.contextPaths, []);
        this.state = DanaState.CONVERSATION;
      } else {
        this.state = DanaState.IDLE;
      }
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

  async onClose(): Promise<void> {}

  private get bodyEl(): HTMLElement {
    return this.containerEl.children[1] as HTMLElement;
  }

  render(): void {
    this.bodyEl.empty();
    this.bodyEl.addClass('dana-panel');

    this.renderHeader(this.bodyEl);
    const content = this.bodyEl.createDiv('dana-content');

    switch (this.state) {
      case DanaState.SETUP:        this.renderSetup(content); break;
      case DanaState.IDLE:         this.renderIdle(content); break;
      case DanaState.LOADING:      this.renderLoading(content); break;
      case DanaState.STREAMING:    this.renderStreaming(content); break;
      case DanaState.DONE:         this.renderConversation(content); break;
      case DanaState.CONVERSATION: this.renderConversation(content); break;
      case DanaState.ERROR_NO_AI:  this.renderErrorNoAI(content); break;
      case DanaState.ERROR_TIMEOUT:  this.renderErrorTimeout(content); break;
      case DanaState.ERROR_NO_NOTES: this.renderErrorNoNotes(content); break;
      case DanaState.EMPTY_NOTES:  this.renderEmptyNotes(content); break;
    }
  }

  // ── Header ───────────────────────────────────────────────────────────────

  private renderHeader(el: HTMLElement): void {
    const header = el.createDiv('dana-header');

    const identity = header.createDiv('dana-identity');
    identity.createSpan({ cls: 'dana-avatar', text: '◉' });
    identity.createSpan({ cls: 'dana-name', text: 'Dana' });

    const gear = header.createEl('button', {
      cls: 'dana-settings-btn',
      attr: { 'aria-label': 'Dana settings' },
    });
    setIcon(gear, 'settings');
    gear.addEventListener('click', () => this.openSettings());
  }

  // ── States ───────────────────────────────────────────────────────────────

  private renderSetup(el: HTMLElement): void {
    const card = el.createDiv('dana-setup-card');
    card.createDiv({ cls: 'dana-setup-avatar', text: '◉' });
    card.createDiv({ cls: 'dana-setup-title', text: 'Meet Dana' });
    card.createDiv({ cls: 'dana-setup-desc', text: 'Your private journaling companion.' });

    const btn = card.createEl('button', { cls: 'dana-btn-primary', text: 'Get started' });
    btn.addEventListener('click', () => {
      this.plugin.settings.onboarded = true;
      this.plugin.saveSettings();
      this.openSettings();
      this.state = DanaState.IDLE;
      this.render();
    });
  }

  private renderIdle(el: HTMLElement): void {
    el.createDiv({
      cls: 'dana-greeting',
      text: this.activeIsJournalNote
        ? this.timeGreeting()
        : 'Open a journal note to reflect on it, or look back at your week.',
    });

    // Reflect on this entry — grounded in the open note ONLY, disabled otherwise
    const entryBtn = el.createEl('button', { cls: 'dana-btn-primary dana-btn-mode' });
    entryBtn.createDiv({ cls: 'dana-btn-label', text: 'Reflect on this entry' });
    const entrySub = entryBtn.createDiv({
      cls: 'dana-btn-subtitle',
      text: this.activeIsJournalNote ? 'the note you have open' : 'open a journal note first',
    });
    entrySub.id = 'dana-entry-subtitle';
    if (!this.activeIsJournalNote) {
      entryBtn.addClass('dana-btn-disabled');
      entryBtn.setAttr('aria-disabled', 'true');
      entryBtn.setAttr('aria-describedby', 'dana-entry-subtitle');
    } else {
      entryBtn.addEventListener('click', () => this.startReflection('entry'));
    }

    // Reflect on my week — last N entries by date
    const weekBtn = el.createEl('button', { cls: 'dana-btn-secondary dana-btn-mode' });
    weekBtn.createDiv({ cls: 'dana-btn-label', text: 'Reflect on my week' });
    weekBtn.createDiv({
      cls: 'dana-btn-subtitle',
      text: `your last ${this.plugin.settings.maxContextEntries} entries`,
    });
    weekBtn.addEventListener('click', () => this.startReflection('week'));
  }

  private renderLoading(el: HTMLElement): void {
    const mode = this.activeSession?.mode;
    el.createDiv({
      cls: 'dana-loading-msg',
      text: mode === 'entry'
        ? 'Dana is reading this note...'
        : 'Dana is reading your recent notes...',
    });
    el.createDiv({ cls: 'dana-dots', text: '• • •' });

    const cancelBtn = el.createEl('button', { cls: 'dana-btn-secondary', text: 'Cancel' });
    cancelBtn.addEventListener('click', () => {
      this.abortCause = 'user';
      this.abortController?.abort();
      this.state = DanaState.IDLE;
      this.render();
    });
  }

  private renderStreaming(el: HTMLElement): void {
    const card = el.createDiv('dana-response-card');
    const text = card.createDiv({ cls: 'dana-response-text', text: this.streamContent });
    text.id = 'dana-stream-target';

    const stopBtn = el.createEl('button', { cls: 'dana-btn-secondary', text: 'Stop' });
    stopBtn.addEventListener('click', () => {
      this.abortCause = 'user';
      this.abortController?.abort();
    });
  }

  private renderConversation(el: HTMLElement): void {
    this.renderThread(el);
    this.renderInput(el);
    this.renderActions(el);
  }

  private renderThread(el: HTMLElement): void {
    const session = this.activeSession;
    if (!session) return;

    const thread = el.createDiv('dana-thread');
    const sourcePath = `${this.plugin.settings.journalFolder}/.dana/${this.conversationDate}-conversation.md`;

    session.messages.forEach((msg, i) => {
      if (msg.role === 'dana') {
        const card = thread.createDiv('dana-response-card');
        const textEl = card.createDiv({ cls: 'dana-response-text' });
        // Render structured markdown; the panel is the Component so render
        // children are cleaned up with the view.
        void MarkdownRenderer.render(this.app, msg.content, textEl, sourcePath, this);
        if (msg.truncated) {
          const marker = card.createDiv('dana-cutoff');
          marker.createSpan({ text: 'Response was cut off' });
          if (i === session.messages.length - 1) {
            const retry = marker.createEl('button', { cls: 'dana-btn-text', text: 'Retry' });
            retry.addEventListener('click', () => this.retryLastResponse());
          }
        }
      } else {
        thread.createDiv({ cls: 'dana-user-msg', text: msg.content });
      }
    });
    thread.scrollTop = thread.scrollHeight;
  }

  private renderInput(el: HTMLElement): void {
    const inputWrap = el.createDiv('dana-input-wrap');
    const input = inputWrap.createEl('textarea', {
      cls: 'dana-input',
      attr: { placeholder: 'Write a response...' },
    });
    input.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const val = input.value.trim();
        if (val) {
          input.value = '';
          this.sendMessage(val);
        }
      }
    });
    setTimeout(() => input.focus(), 50);
  }

  private renderActions(el: HTMLElement): void {
    const actions = el.createDiv('dana-actions');

    const copyBtn = actions.createEl('button', { cls: 'dana-btn-ghost', text: 'Copy' });
    copyBtn.addEventListener('click', () => {
      const msgs = this.activeSession?.messages ?? [];
      const last = [...msgs].reverse().find(m => m.role === 'dana');
      if (last) {
        navigator.clipboard.writeText(last.content);
        new Notice('Copied');
      }
    });

    const freshBtn = actions.createEl('button', { cls: 'dana-btn-ghost', text: 'Start fresh' });
    freshBtn.addEventListener('click', () => {
      // Earlier sessions stay in today's file; the next reflection appends a
      // new session block instead of overwriting them.
      this.streamContent = '';
      this.snapshot = [];
      this.state = DanaState.IDLE;
      this.render();
    });
  }

  private renderErrorNoAI(el: HTMLElement): void {
    const card = el.createDiv('dana-error-card');
    card.createDiv({ cls: 'dana-error-msg', text: 'Dana needs a brain to reflect with you.' });
    const btn = card.createEl('button', { cls: 'dana-btn-primary', text: 'Set up AI →' });
    btn.addEventListener('click', () => this.openSettings());
  }

  private renderErrorTimeout(el: HTMLElement): void {
    const card = el.createDiv('dana-error-card');
    card.createDiv({ cls: 'dana-error-msg', text: 'Something went wrong.' });
    if (this.lastError) {
      card.createDiv({ cls: 'dana-error-detail', text: this.lastError });
    }
    const actions = card.createDiv('dana-actions');
    const retry = actions.createEl('button', { cls: 'dana-btn-primary', text: 'Retry' });
    retry.addEventListener('click', () => this.retryLastResponse());
    const cancel = actions.createEl('button', { cls: 'dana-btn-secondary', text: 'Cancel' });
    cancel.addEventListener('click', () => { this.state = DanaState.IDLE; this.render(); });
  }

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

  private renderEmptyNotes(el: HTMLElement): void {
    const card = el.createDiv('dana-error-card');
    card.createDiv({
      cls: 'dana-error-msg',
      text: "Write a few more lines and I'll reflect with you.",
    });
    const btn = card.createEl('button', { cls: 'dana-btn-ghost', text: 'Dismiss' });
    btn.addEventListener('click', () => { this.state = DanaState.IDLE; this.render(); });
  }

  // ── Core logic ───────────────────────────────────────────────────────────

  /** Begin a new conversation in the given mode. Context is resolved once. */
  async startReflection(mode: ReflectionMode): Promise<void> {
    this.state = DanaState.LOADING;
    this.render();

    const activeFile = this.app.workspace.getActiveFile();
    const frontmatter = activeFile
      ? this.app.metadataCache.getFileCache(activeFile)?.frontmatter ?? null
      : null;

    const { entries, activeIsJournalNote } = await this.contextResolver.resolve(
      mode,
      activeFile,
      frontmatter,
      this.plugin.settings
    );
    this.activeIsJournalNote = activeIsJournalNote;

    if (entries.length === 0) {
      if (mode === 'entry') {
        if (!activeIsJournalNote) {
          // Only reachable via command palette race — the button is disabled.
          new Notice('Open a journal note first');
          this.state = DanaState.IDLE;
        } else {
          this.state = DanaState.EMPTY_NOTES; // note exists but under 50 chars
        }
      } else {
        this.state = DanaState.ERROR_NO_NOTES;
      }
      this.render();
      return;
    }

    this.conversationDate = this.conversationStore.localToday();
    this.sessions.push({
      mode,
      contextPaths: entries.map(e => e.path),
      messages: [],
    });
    this.snapshot = entries;

    await this.generateTurn();
  }

  /** Follow-up turn in the pinned conversation. */
  async sendMessage(content: string): Promise<void> {
    if (!this.activeSession) return;
    await this.generateTurn(content);
  }

  /** Drop the last (cut-off or errored) Dana response and regenerate. */
  private async retryLastResponse(): Promise<void> {
    const session = this.activeSession;
    if (!session) {
      this.state = DanaState.IDLE;
      this.render();
      return;
    }
    const msgs = session.messages;
    if (msgs.length > 0 && msgs[msgs.length - 1].role === 'dana') {
      msgs.pop();
    }
    await this.generateTurn();
  }

  /** Re-read a pinned context path list; fall back to snapshot per file. */
  private async readPinned(paths: string[], snapshot: JournalEntry[]): Promise<JournalEntry[]> {
    const entries: JournalEntry[] = [];
    for (const path of paths) {
      const fresh = await this.vaultReader.readPath(path);
      if (fresh) {
        entries.push(fresh);
      } else {
        const fallback = snapshot.find(e => e.path === path);
        if (fallback) entries.push(fallback);
      }
    }
    return entries;
  }

  private async generateTurn(userInput?: string): Promise<void> {
    const session = this.activeSession;
    if (!session) return;

    this.abortController = new AbortController();
    this.abortCause = null;
    this.streamContent = '';
    this.lastError = '';
    this.state = DanaState.LOADING;
    this.render();

    // 30s to first token; once streaming, 60s between tokens.
    let timer: ReturnType<typeof setTimeout> | undefined;
    const arm = (cause: 'ttft' | 'idle', ms: number) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        this.abortCause = cause;
        this.abortController?.abort();
      }, ms);
    };
    arm('ttft', 30_000);

    try {
      // Re-read pinned files — the user edits notes mid-conversation and Dana
      // must quote the current text, not a stale snapshot.
      const entries = await this.readPinned(session.contextPaths, this.snapshot);

      const provider = this.resolveProvider();
      if (!provider || !(await provider.isAvailable())) {
        this.state = DanaState.ERROR_NO_AI;
        this.render();
        return;
      }

      const systemPrompt = this.promptBuilder.buildSystemPrompt(session.mode, entries);
      const apiMessages = this.promptBuilder.buildTurnMessages(session.mode, session.messages, userInput);

      if (userInput) {
        session.messages.push({ role: 'user', content: userInput, timestamp: Date.now() });
      }

      console.debug('[Dana] turn', {
        mode: session.mode,
        entries: entries.length,
        contextChars: systemPrompt.length,
        provider: provider.name,
      });

      this.state = DanaState.STREAMING;
      this.render();

      const signal = this.abortController.signal;
      let response = '';
      let truncated = false;

      // Manual iteration: for-await discards the generator's return value,
      // which carries the token-cap truncation flag.
      const stream = provider.generate(systemPrompt, apiMessages, signal);
      while (true) {
        const { done, value } = await stream.next();
        if (done) {
          truncated = value?.truncated ?? false;
          break;
        }
        if (signal.aborted) break;
        arm('idle', 60_000);
        response += value;
        this.streamContent = response;
        const target = document.getElementById('dana-stream-target');
        if (target) target.textContent = response;
      }

      this.finishTurn(session, response, truncated);
    } catch (err: unknown) {
      // Classify by the cause we set BEFORE aborting — rejection values are
      // not reliable (fetch can reject with plain strings or DOMExceptions).
      if (this.abortCause === 'user' || this.abortCause === 'idle') {
        this.finishTurn(session, this.streamContent, true);
      } else if (this.abortCause === 'ttft') {
        console.error('Dana timeout before first token:', err);
        this.lastError = 'No response after 30s. Is your AI provider running?';
        this.state = DanaState.ERROR_TIMEOUT;
        this.render();
      } else {
        console.error('Dana error:', err);
        this.lastError = err instanceof Error ? err.message : String(err);
        this.state = DanaState.ERROR_TIMEOUT;
        this.render();
      }
    } finally {
      clearTimeout(timer);
    }
  }

  private finishTurn(session: ConversationSession, response: string, truncated: boolean): void {
    const text = response.trim();
    if (text) {
      session.messages.push({
        role: 'dana',
        content: text,
        timestamp: Date.now(),
        ...(truncated ? { truncated: true } : {}),
      });
      void this.conversationStore.save(
        this.plugin.settings.journalFolder,
        this.conversationDate,
        this.sessions
      );
      this.state = DanaState.DONE;
    } else {
      this.state = session.messages.length > 0 ? DanaState.CONVERSATION : DanaState.IDLE;
    }
    this.render();
  }

  // ── Helpers ──────────────────────────────────────────────────────────────

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

  private timeGreeting(): string {
    const h = new Date().getHours();
    if (h >= 5 && h < 12) return "Good morning. What's on your mind as the day begins?";
    if (h >= 12 && h < 18) return "How's the day going so far?";
    return "How are you winding down?";
  }

  private openSettings(): void {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const s = (this.app as any).setting;
    s?.open?.();
    s?.openTabById?.(this.plugin.manifest.id);
  }
}
