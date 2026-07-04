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
