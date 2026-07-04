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

const settings = { journalFolder: 'Daily Notes', maxContextEntries: 7 };

describe('ContextResolver.resolve — entry mode', () => {
  it('returns ONLY the active journal note, never touching recent entries', async () => {
    const activeEntry = makeEntry('Daily Notes/2026-07-04.md', '2026-07-04', 'today content');
    const vaultReader = {
      readRecentEntries: jest.fn(),
      readActiveFile: jest.fn().mockResolvedValue(activeEntry),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(true) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve('entry', makeFile('Daily Notes/2026-07-04.md'), null, settings);

    expect(result.entries).toEqual([activeEntry]);
    expect(vaultReader.readRecentEntries).not.toHaveBeenCalled();
  });

  it('returns empty when the active note is not a journal note', async () => {
    const vaultReader = {
      readRecentEntries: jest.fn(),
      readActiveFile: jest.fn(),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(false) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve('entry', makeFile('Projects/work.md'), null, settings);

    expect(result.entries).toEqual([]);
    expect(result.activeIsJournalNote).toBe(false);
    expect(vaultReader.readActiveFile).not.toHaveBeenCalled();
  });

  it('returns empty when no note is open', async () => {
    const vaultReader = { readRecentEntries: jest.fn(), readActiveFile: jest.fn() };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(false) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve('entry', null, null, settings);

    expect(result.entries).toEqual([]);
  });

  it('returns empty when the active note is a journal note but too short to read', async () => {
    const vaultReader = {
      readRecentEntries: jest.fn(),
      readActiveFile: jest.fn().mockResolvedValue(null),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(true) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve('entry', makeFile('Daily Notes/2026-07-04.md'), null, settings);

    expect(result.entries).toEqual([]);
    expect(result.activeIsJournalNote).toBe(true);
  });
});

describe('ContextResolver.resolve — week mode', () => {
  it('returns recent entries oldest-to-newest', async () => {
    const recent = [
      makeEntry('Daily Notes/2026-07-04.md', '2026-07-04'),
      makeEntry('Daily Notes/2026-07-03.md', '2026-07-03'),
    ];
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue(recent),
      readActiveFile: jest.fn(),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(false) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve('week', makeFile('Projects/work.md'), null, settings);

    expect(result.entries.map(e => e.date)).toEqual(['2026-07-03', '2026-07-04']);
    expect(vaultReader.readActiveFile).not.toHaveBeenCalled();
  });

  it('appends the active journal note when not already in the recent scan', async () => {
    const recent = [makeEntry('Daily Notes/2026-07-03.md', '2026-07-03')];
    const activeEntry = makeEntry('Notes/2026-07-04.md', '2026-07-04', 'today content');
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue(recent),
      readActiveFile: jest.fn().mockResolvedValue(activeEntry),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(true) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve('week', makeFile('Notes/2026-07-04.md'), null, settings);

    expect(result.entries).toEqual([recent[0], activeEntry]);
  });

  it('does not duplicate the active note when it is already in the recent scan', async () => {
    const activePath = 'Daily Notes/2026-07-04.md';
    const recent = [
      makeEntry(activePath, '2026-07-04'),
      makeEntry('Daily Notes/2026-07-03.md', '2026-07-03'),
    ];
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue(recent),
      readActiveFile: jest.fn(),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(true) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve('week', makeFile(activePath), null, settings);

    expect(result.entries).toHaveLength(2);
    expect(vaultReader.readActiveFile).not.toHaveBeenCalled();
  });

  it('respects maxContextEntries = 1 boundary', async () => {
    const recent = [makeEntry('Daily Notes/2026-07-04.md', '2026-07-04')];
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue(recent),
      readActiveFile: jest.fn(),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(false) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve('week', null, null, {
      journalFolder: 'Daily Notes',
      maxContextEntries: 1,
    });

    expect(vaultReader.readRecentEntries).toHaveBeenCalledWith('Daily Notes', 1);
    expect(result.entries).toHaveLength(1);
  });

  it('returns an empty result when there are no entries anywhere', async () => {
    const vaultReader = {
      readRecentEntries: jest.fn().mockResolvedValue([]),
      readActiveFile: jest.fn(),
    };
    const journalDetector = { isJournalNote: jest.fn().mockReturnValue(false) };
    const resolver = new ContextResolver(vaultReader, journalDetector);

    const result = await resolver.resolve('week', null, null, settings);

    expect(result.entries).toEqual([]);
  });
});
