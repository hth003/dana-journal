import { TFile } from 'obsidian';

const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const JOURNAL_TAGS = new Set(['journal', 'daily', 'diary']);

export class JournalDetector {
  isJournalNote(
    file: TFile | null,
    journalFolder: string,
    frontmatter?: Record<string, unknown> | null
  ): boolean {
    if (!file) return false;

    // Priority 1: frontmatter tags contain journal/daily
    if (frontmatter?.tags) {
      const tags = Array.isArray(frontmatter.tags)
        ? frontmatter.tags
        : [frontmatter.tags];
      if (tags.some((t: unknown) => JOURNAL_TAGS.has(String(t).toLowerCase()))) {
        return true;
      }
    }

    // Priority 2: filename matches YYYY-MM-DD
    if (DATE_PATTERN.test(file.basename)) return true;

    // Priority 3: inside configured journal folder
    if (journalFolder) {
      const folder = journalFolder.replace(/\/$/, '');
      if (file.path.startsWith(folder + '/')) return true;
    }

    return false;
  }
}
