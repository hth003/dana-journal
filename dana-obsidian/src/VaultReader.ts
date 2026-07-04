import { App, TFile } from 'obsidian';
import { JournalEntry } from './types';

const MAX_ENTRY_CHARS = 2000;
const MIN_ENTRY_CHARS = 50;

// Patterns that could be prompt injection attempts
const INJECTION_PATTERNS = [
  /\bignore\s+(previous|above|all|prior)\b/gi,
  /\bsystem\s*:\s*/gi,
  /\bnew\s+instruction[s]?\b/gi,
  /\bforget\s+(everything|all|previous)\b/gi,
];

export class VaultReader {
  constructor(private app: App) {}

  async readActiveFile(file: TFile): Promise<JournalEntry | null> {
    return this.readFile(file);
  }

  /** Re-read a pinned context file by path. Null if it no longer exists. */
  async readPath(path: string): Promise<JournalEntry | null> {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (!(file instanceof TFile)) return null;
    return this.readFile(file);
  }

  async readRecentEntries(folderPath: string, maxEntries: number): Promise<JournalEntry[]> {
    const allFiles = this.app.vault.getMarkdownFiles();

    const filtered = folderPath
      ? allFiles.filter(f => f.path.startsWith(folderPath.replace(/\/$/, '') + '/') || f.path === folderPath)
      : allFiles;

    // "Recent" means recent DAYS, not recently touched: sort by the date in the
    // filename (YYYY-MM-DD) so editing an old note doesn't promote it. Files
    // without a parseable date fall back to their mtime on the same ms scale.
    const sorted = filtered.slice().sort((a, b) => this.entryTime(b) - this.entryTime(a));

    const entries: JournalEntry[] = [];
    for (const file of sorted) {
      if (entries.length >= maxEntries) break;
      const entry = await this.readFile(file);
      if (entry) entries.push(entry);
    }

    return entries;
  }

  private entryTime(file: TFile): number {
    const m = file.basename.match(/(\d{4})-(\d{2})-(\d{2})/);
    if (m) {
      const t = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])).getTime();
      if (!Number.isNaN(t)) return t;
    }
    return file.stat.mtime;
  }

  private async readFile(file: TFile): Promise<JournalEntry | null> {
    try {
      const raw = await this.app.vault.cachedRead(file);
      const content = this.parseEntry(raw);
      if (!content) return null;
      return {
        date: file.basename,
        content: this.sanitizeForPrompt(content),
        path: file.path,
      };
    } catch {
      return null;
    }
  }

  parseEntry(raw: string): string | null {
    let content = raw.trim();

    // Strip YAML frontmatter
    if (content.startsWith('---')) {
      const closeIdx = content.indexOf('---', 3);
      if (closeIdx !== -1) {
        content = content.slice(closeIdx + 3).trim();
      }
    }

    if (content.length < MIN_ENTRY_CHARS) return null;

    // Strip markdown structure (headers, wikilinks, external links) — keep prose
    content = content
      .replace(/^#{1,6}\s+/gm, '')
      .replace(/\[\[(?:[^\]|]+\|)?([^\]]+)\]\]/g, '$1')
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      .replace(/!\[.*?\]\([^)]+\)/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    if (content.length < MIN_ENTRY_CHARS) return null;

    // Truncate at sentence boundary
    if (content.length > MAX_ENTRY_CHARS) {
      const truncated = content.slice(0, MAX_ENTRY_CHARS);
      const lastPeriod = truncated.lastIndexOf('.');
      content = lastPeriod > MAX_ENTRY_CHARS * 0.8
        ? truncated.slice(0, lastPeriod + 1)
        : truncated + '...';
    }

    return content;
  }

  sanitizeForPrompt(content: string): string {
    let safe = content;
    for (const pattern of INJECTION_PATTERNS) {
      safe = safe.replace(pattern, '[...]');
    }
    return safe;
  }
}
