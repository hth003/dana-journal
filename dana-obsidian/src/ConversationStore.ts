import { App, TFile } from 'obsidian';
import { ConversationMessage, ConversationSession } from './types';

/**
 * Conversation file format v2 — {journalFolder}/.dana/YYYY-MM-DD-conversation.md
 *
 *   ---
 *   version: 2
 *   date: 2026-07-04
 *   ---
 *   <!-- dana:session {"mode":"entry","contextPaths":["Journal/2026-07-04.md"]} -->
 *   <!-- dana:msg role=dana -->
 *   multi-paragraph markdown, renders clean in reading view
 *   <!-- dana:msg role=user -->
 *   ...
 *
 * HTML-comment delimiters are invisible in Obsidian's reading view and cannot
 * collide with anything a user types as prose — these files are hand-editable
 * by design. The date key is LOCAL time (an 8pm conversation in California
 * belongs to today, not tomorrow UTC) and callers pass the conversation-START
 * date so a chat crossing midnight stays in the file it began in.
 */

const SESSION_MARKER = /^<!-- dana:session(?: (.*?))? -->$/;
const MSG_MARKER = /^<!-- dana:msg role=(dana|user)( truncated=true)? -->$/;

export class ConversationStore {
  constructor(private app: App) {}

  localToday(): string {
    const d = new Date();
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  private buildPath(journalFolder: string, date: string): string {
    const base = journalFolder ? journalFolder.replace(/\/$/, '') : '';
    return base ? `${base}/.dana/${date}-conversation.md` : `.dana/${date}-conversation.md`;
  }

  async load(journalFolder: string, date: string): Promise<ConversationSession[]> {
    const path = this.buildPath(journalFolder, date);
    const file = this.app.vault.getAbstractFileByPath(path);
    if (!(file instanceof TFile)) return [];
    try {
      const content = await this.app.vault.cachedRead(file);
      return this.parse(content);
    } catch {
      return [];
    }
  }

  async save(journalFolder: string, date: string, sessions: ConversationSession[]): Promise<void> {
    const nonEmpty = sessions.filter(s => s.messages.length > 0);
    if (nonEmpty.length === 0) return;

    const path = this.buildPath(journalFolder, date);
    const content = this.serialize(date, nonEmpty);

    const existing = this.app.vault.getAbstractFileByPath(path);
    if (existing instanceof TFile) {
      await this.app.vault.modify(existing, content);
      return;
    }

    // Ensure .dana/ directory exists — ignore "already exists" errors
    const dir = path.substring(0, path.lastIndexOf('/'));
    if (dir) {
      try {
        await this.app.vault.createFolder(dir);
      } catch {
        // folder already exists, that's fine
      }
    }

    // File may have been created between our check and now
    try {
      await this.app.vault.create(path, content);
    } catch {
      const created = this.app.vault.getAbstractFileByPath(path);
      if (created instanceof TFile) {
        await this.app.vault.modify(created, content);
      }
    }
  }

  serialize(date: string, sessions: ConversationSession[]): string {
    const parts: string[] = [`---\nversion: 2\ndate: ${date}\n---`];
    for (const session of sessions) {
      const attrs = JSON.stringify({ mode: session.mode, contextPaths: session.contextPaths });
      parts.push(`<!-- dana:session ${attrs} -->`);
      for (const msg of session.messages) {
        const truncated = msg.truncated ? ' truncated=true' : '';
        // A typed message could contain a literal marker line — escape it so
        // it round-trips as content instead of splitting the file.
        const safe = msg.content
          .trim()
          .split('\n')
          .map(l => (SESSION_MARKER.test(l) || MSG_MARKER.test(l) ? `\\${l}` : l))
          .join('\n');
        parts.push(`<!-- dana:msg role=${msg.role}${truncated} -->\n${safe}`);
      }
    }
    return parts.join('\n\n') + '\n';
  }

  parse(content: string): ConversationSession[] {
    let body = content;
    if (body.startsWith('---')) {
      const close = body.indexOf('\n---', 3);
      if (close !== -1) body = body.slice(close + 4);
    }

    if (!/^<!-- dana:(session|msg)/m.test(body)) {
      return this.parseLegacyV1(body);
    }

    const sessions: ConversationSession[] = [];
    let current: ConversationSession | null = null;
    let message: ConversationMessage | null = null;
    const contentLines: string[] = [];

    const flushMessage = () => {
      if (message && current) {
        message.content = contentLines.join('\n').trim();
        if (message.content) current.messages.push(message);
      }
      message = null;
      contentLines.length = 0;
    };

    for (const line of body.split('\n')) {
      const sessionMatch = line.match(SESSION_MARKER);
      if (sessionMatch) {
        flushMessage();
        current = { mode: 'week', contextPaths: [], messages: [] };
        try {
          const attrs = JSON.parse(sessionMatch[1] ?? '{}');
          if (attrs.mode === 'entry' || attrs.mode === 'week') current.mode = attrs.mode;
          if (Array.isArray(attrs.contextPaths)) {
            current.contextPaths = attrs.contextPaths.filter((p: unknown) => typeof p === 'string');
          }
        } catch {
          // malformed attrs — keep defaults, don't lose the messages
        }
        sessions.push(current);
        continue;
      }

      const msgMatch = line.match(MSG_MARKER);
      if (msgMatch) {
        flushMessage();
        if (!current) {
          // msg marker before any session marker — tolerate hand-edited files
          current = { mode: 'week', contextPaths: [], messages: [] };
          sessions.push(current);
        }
        message = {
          role: msgMatch[1] === 'dana' ? 'dana' : 'user',
          content: '',
          timestamp: 0,
          ...(msgMatch[2] ? { truncated: true } : {}),
        };
        continue;
      }

      if (message) {
        // unescape marker lines that were stored as content
        contentLines.push(line.startsWith('\\<!-- dana:') ? line.slice(1) : line);
      }
    }
    flushMessage();

    return sessions.filter(s => s.messages.length > 0);
  }

  /** Pre-v2 files: alternating "**Dana:**" / "**Me:**" blocks, single session. */
  private parseLegacyV1(content: string): ConversationSession[] {
    const messages: ConversationMessage[] = [];
    for (const block of content.split('\n\n')) {
      const trimmed = block.trim();
      if (trimmed.startsWith('**Dana:**')) {
        messages.push({ role: 'dana', content: trimmed.slice(9).trim(), timestamp: 0 });
      } else if (trimmed.startsWith('**Me:**')) {
        messages.push({ role: 'user', content: trimmed.slice(7).trim(), timestamp: 0 });
      }
    }
    if (messages.length === 0) return [];
    return [{ mode: 'week', contextPaths: [], messages }];
  }
}
