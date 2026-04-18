import { JournalDetector } from '../src/JournalDetector';

const detector = new JournalDetector();

function makeFile(path: string) {
  const parts = path.split('/');
  const name = parts[parts.length - 1];
  return { path, basename: name.replace('.md', ''), stat: { mtime: 0, ctime: 0, size: 0 } } as any;
}

describe('JournalDetector.isJournalNote', () => {
  it('returns false for null file', () => {
    expect(detector.isJournalNote(null, '')).toBe(false);
  });

  it('detects journal tag in frontmatter', () => {
    const file = makeFile('Notes/thoughts.md');
    expect(detector.isJournalNote(file, '', { tags: ['journal', 'ideas'] })).toBe(true);
  });

  it('detects daily tag in frontmatter', () => {
    const file = makeFile('Notes/today.md');
    expect(detector.isJournalNote(file, '', { tags: ['daily'] })).toBe(true);
  });

  it('is case-insensitive for tags', () => {
    const file = makeFile('Notes/today.md');
    expect(detector.isJournalNote(file, '', { tags: ['Journal'] })).toBe(true);
    expect(detector.isJournalNote(file, '', { tags: ['DAILY'] })).toBe(true);
  });

  it('detects YYYY-MM-DD filename pattern', () => {
    const file = makeFile('Notes/2026-04-18.md');
    expect(detector.isJournalNote(file, '')).toBe(true);
  });

  it('does not match partial date patterns', () => {
    const file = makeFile('Notes/2026-4-18.md');
    expect(detector.isJournalNote(file, '')).toBe(false);
  });

  it('detects file inside configured journal folder', () => {
    const file = makeFile('Daily Notes/thoughts.md');
    expect(detector.isJournalNote(file, 'Daily Notes')).toBe(true);
  });

  it('does not match file outside configured folder', () => {
    const file = makeFile('Projects/work.md');
    expect(detector.isJournalNote(file, 'Daily Notes')).toBe(false);
  });

  it('handles folder path with trailing slash', () => {
    const file = makeFile('Daily Notes/2026-04-18.md');
    expect(detector.isJournalNote(file, 'Daily Notes/')).toBe(true);
  });

  it('returns false with no folder and no tags and non-date filename', () => {
    const file = makeFile('Notes/random-thoughts.md');
    expect(detector.isJournalNote(file, '')).toBe(false);
  });
});
