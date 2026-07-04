import type { TFile } from 'obsidian';
import { JournalEntry, ReflectionMode } from './types';

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

/**
 * Decides what journal content grounds a reflection. The mode is the contract
 * shown on the button the user pressed — never widen it:
 *
 *   mode 'entry' ──▶ [the active journal note]           (exactly one file)
 *   mode 'week'  ──▶ [last N entries by date, oldest→newest, active deduped]
 *
 * 'entry' with a non-journal active note returns empty entries — callers gate
 * this in the UI, but resolve() stays safe if they don't.
 */
export class ContextResolver {
  constructor(private vaultReader: RecentEntryReader, private journalDetector: NoteClassifier) {}

  async resolve(
    mode: ReflectionMode,
    activeFile: TFile | null,
    frontmatter: Record<string, unknown> | null,
    settings: ContextSettings
  ): Promise<ResolvedContext> {
    const activeIsJournalNote = this.journalDetector.isJournalNote(
      activeFile,
      settings.journalFolder,
      frontmatter
    );

    if (mode === 'entry') {
      if (!activeFile || !activeIsJournalNote) {
        return { entries: [], activeIsJournalNote };
      }
      const entry = await this.vaultReader.readActiveFile(activeFile);
      return { entries: entry ? [entry] : [], activeIsJournalNote };
    }

    // week mode
    const recent = await this.vaultReader.readRecentEntries(
      settings.journalFolder,
      settings.maxContextEntries
    );
    // readRecentEntries returns most-recent-first; we want oldest-to-newest for prompting
    const entries = recent.slice().reverse();

    if (activeFile && activeIsJournalNote && !entries.some(e => e.path === activeFile.path)) {
      const activeEntry = await this.vaultReader.readActiveFile(activeFile);
      if (activeEntry) {
        entries.push(activeEntry);
      }
    }

    return { entries, activeIsJournalNote };
  }
}
