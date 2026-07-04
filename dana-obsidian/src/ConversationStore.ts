import { App, TFile } from 'obsidian';
import { ConversationMessage } from './types';

export class ConversationStore {
  constructor(private app: App) {}

  private buildPath(journalFolder: string, date: string): string {
    const base = journalFolder ? journalFolder.replace(/\/$/, '') : '';
    return base ? `${base}/.dana/${date}-conversation.md` : `.dana/${date}-conversation.md`;
  }

  private todayISO(): string {
    return new Date().toISOString().slice(0, 10);
  }

  async loadToday(journalFolder: string): Promise<ConversationMessage[]> {
    const path = this.buildPath(journalFolder, this.todayISO());
    const file = this.app.vault.getAbstractFileByPath(path);
    if (!(file instanceof TFile)) return [];
    try {
      const content = await this.app.vault.cachedRead(file);
      return this.parseMarkdown(content);
    } catch {
      return [];
    }
  }

  async save(journalFolder: string, messages: ConversationMessage[]): Promise<void> {
    if (messages.length === 0) return;

    const path = this.buildPath(journalFolder, this.todayISO());
    const content = messages
      .map(m => `**${m.role === 'dana' ? 'Dana' : 'Me'}:** ${m.content}`)
      .join('\n\n');

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

  private parseMarkdown(content: string): ConversationMessage[] {
    const messages: ConversationMessage[] = [];
    for (const block of content.split('\n\n')) {
      const trimmed = block.trim();
      if (trimmed.startsWith('**Dana:**')) {
        messages.push({ role: 'dana', content: trimmed.slice(9).trim(), timestamp: 0 });
      } else if (trimmed.startsWith('**Me:**')) {
        messages.push({ role: 'user', content: trimmed.slice(7).trim(), timestamp: 0 });
      }
    }
    return messages;
  }
}
