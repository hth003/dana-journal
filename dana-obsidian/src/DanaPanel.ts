import { ItemView, Notice, WorkspaceLeaf, setIcon } from 'obsidian';
import { DanaState, ConversationMessage } from './types';
import { VaultReader } from './VaultReader';
import { ConversationStore } from './ConversationStore';
import { PromptBuilder } from './PromptBuilder';
import { ContextResolver } from './ContextResolver';
import { OllamaProvider } from './providers/OllamaProvider';
import { OpenAIProvider } from './providers/OpenAIProvider';
import type { AIProvider, ChatMessage } from './providers/AIProvider';
import type DanaPlugin from '../main';

export const VIEW_TYPE_DANA = 'dana-journal-view';

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
      case DanaState.DONE:         this.renderDone(content); break;
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
    const greeting = el.createDiv({
      cls: 'dana-greeting',
      text: this.activeIsJournalNote
        ? this.timeGreeting()
        : 'Open a journal note to reflect on today, or explore recent patterns.',
    });

    const primaryBtn = el.createEl('button', {
      cls: 'dana-btn-primary',
      text: 'Reflect on today',
    });
    primaryBtn.addEventListener('click', () => this.reflect());

    const chips = el.createDiv('dana-chips');
    for (const prompt of ['What\'s been on my mind?', 'Process a feeling', 'How have I been lately?']) {
      const chip = chips.createEl('button', { cls: 'dana-chip', text: prompt });
      chip.addEventListener('click', () => this.reflect(prompt));
    }

    const footer = el.createDiv({ cls: 'dana-footer-note' });
    footer.setText(`Reading ${this.plugin.settings.maxContextEntries} recent notes`);
  }

  private renderLoading(el: HTMLElement): void {
    el.createDiv({ cls: 'dana-loading-msg', text: 'Dana is reading your recent notes...' });
    el.createDiv({ cls: 'dana-dots', text: '• • •' });

    const cancelBtn = el.createEl('button', { cls: 'dana-btn-secondary', text: 'Cancel' });
    cancelBtn.addEventListener('click', () => {
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
    stopBtn.addEventListener('click', () => this.abortController?.abort());
  }

  private renderDone(el: HTMLElement): void {
    this.renderThread(el);
    this.renderInput(el);
    this.renderDoneActions(el);
  }

  private renderConversation(el: HTMLElement): void {
    this.renderThread(el);
    this.renderInput(el);
    this.renderDoneActions(el);
  }

  private renderThread(el: HTMLElement): void {
    const thread = el.createDiv('dana-thread');
    for (const msg of this.messages) {
      if (msg.role === 'dana') {
        const card = thread.createDiv('dana-response-card');
        card.createDiv({ cls: 'dana-response-text', text: msg.content });
      } else {
        thread.createDiv({ cls: 'dana-user-msg', text: msg.content });
      }
    }
    // Scroll to bottom
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
    // Focus the input when conversation is shown
    setTimeout(() => input.focus(), 50);
  }

  private renderDoneActions(el: HTMLElement): void {
    const actions = el.createDiv('dana-actions');

    const copyBtn = actions.createEl('button', { cls: 'dana-btn-ghost', text: 'Copy' });
    copyBtn.addEventListener('click', () => {
      const last = [...this.messages].reverse().find(m => m.role === 'dana');
      if (last) {
        navigator.clipboard.writeText(last.content);
        new Notice('Copied');
      }
    });

    const freshBtn = actions.createEl('button', { cls: 'dana-btn-ghost', text: 'Start fresh' });
    freshBtn.addEventListener('click', () => {
      this.messages = [];
      this.streamContent = '';
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
    retry.addEventListener('click', () => this.reflect());
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
    card.createDiv({ cls: 'dana-error-msg', text: 'Start writing, and Dana will reflect with you.' });
    const btn = card.createEl('button', { cls: 'dana-btn-ghost', text: 'Dismiss' });
    btn.addEventListener('click', () => { this.state = DanaState.IDLE; this.render(); });
  }

  // ── Core logic ───────────────────────────────────────────────────────────

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

  async sendMessage(content: string): Promise<void> {
    await this.reflect(content);
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
