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
